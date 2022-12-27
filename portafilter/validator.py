from copy import deepcopy
from typing import Tuple, Any, List
from portafilter.enums import ValueType
from portafilter.exceptions import ValidationError
from portafilter.json_schema import JsonSchema
from portafilter.rules import RuleList, Ruleset


class Validator:

    def __init__(self, data: dict, rules: dict):
        """The init method

        Arguments:
            data {dict} -- The input data.
            rules {dict} -- The validation rules.
        """
        self._data = data
        self._rules = RuleList(rules)
        self._errors = {}

    def validate(self) -> None:
        """Validate the input data

        Raises:
            ValidationError
        """
        extra_rules = []

        for attribute, ruleset in self._rules:

            try:
                ruleset = self._modify_dependent_rules(ruleset)

                value_details = JsonSchema(self._data).get_value_details(attribute)

                if isinstance(value_details, list):

                    for list_item in value_details:
                        ruleset_clone = deepcopy(ruleset)
                        item_attribute, item_value_details = self._extract_list_details(attribute, list_item)

                        try:
                            item_value, value_exists = item_value_details

                            ruleset_clone.validate(
                                attribute=item_attribute,
                                value=item_value,
                                value_exists=value_exists
                            )

                            # TODO: Pass the value existed to the extra data and set the ruleset with default metadata
                            # TODO: You can add a method called set_rule_metadata and keep the metadata in ruleset too.
                            extra_rules += self._get_extra_rules(item_attribute, item_value, ruleset_clone)

                        except ValidationError as e:
                            self._errors[item_attribute] = ruleset_clone.errors()

                else:
                    value, value_exists = value_details

                    ruleset.validate(attribute=attribute, value=value, value_exists=value_exists)

                    # TODO: Pass the value existed to the extra data and set the ruleset with default metadata
                    # TODO: You can add a method called set_rule_metadata and keep the metadata in ruleset too.
                    extra_rules += self._get_extra_rules(attribute, value, ruleset)

            except ValidationError as e:
                self._errors[attribute] = ruleset.errors()

        # Validate the extra rules
        for extra_attribute, extra_rule, extra_value in extra_rules:
            try:
                extra_rule.validate(extra_attribute, extra_value)

            except ValidationError as e:
                self._errors[extra_attribute] = extra_rule.errors()

        if self.has_error():
            raise ValidationError

    def _extract_list_details(self, attribute: str, list_details: Tuple[int, Any]) -> Tuple[str, Any]:
        """Extract the list details

        Arguments:
            attribute {str}
            list_details {Tuple[int, Any]}

        Returns:
            Tuple[str, Any] -- The tuple of the attribute and the value.
        """
        _index, _value = list_details
        attribute = attribute.replace('.*', f'.{_index}', 1)
        if isinstance(_value, list) and _value and isinstance(_value[0], tuple):
            # Recursive
            attribute, _value = self._extract_list_details(attribute, _value[0])

        return attribute, _value

    @staticmethod
    def _get_extra_rules(attribute: str, value: Any, ruleset: Ruleset) -> List[Tuple[str, Ruleset, Any]]:
        """Get the extra rules

        Arguments:
            attribute {str}
            value {Any}
            ruleset {Ruleset}

        Returns:
            List[Tuple[str, Ruleset, Any]]
        """
        extra_rules = []

        if ruleset.get_value_type() == ValueType.DICT:
            for dict_parameter in ruleset.get_rule('dict').get_params():
                extra_attribute = f'{attribute}.{dict_parameter}'

                try:
                    extra_rule_value = value.get(dict_parameter)

                except Exception as e:
                    extra_rule_value = None

                extra_rules.append((extra_attribute, Ruleset('required'), extra_rule_value))

        return extra_rules

    def has_error(self) -> bool:
        """Check the failure status.

        Returns:
            bool
        """
        return True if self._errors else False

    def fails(self) -> bool:
        """Check the status of the validation

        Returns:
            bool
        """
        try:
            self.validate()

        except ValidationError as e:
            pass

        return self.has_error()

    def passes(self) -> bool:
        """Check the status of the validation

        Returns:
            bool
        """
        try:
            self.validate()

        except ValidationError as e:
            pass

        return not self.has_error()

    def errors(self) -> dict:
        """Get the errors

        Returns:
            dict
        """
        return self._errors

    def _modify_dependent_rules(self, ruleset: Ruleset) -> Ruleset:
        """Modify relational rules

        Arguments:
            ruleset (Ruleset)

        Returns:
            Ruleset
        """
        # The rules are mutable object
        if ruleset.has_rule('same'):
            same_rule = ruleset.get_rule('same')
            other_attribute = same_rule.get_params()[0]
            other_value_details = JsonSchema(self._data).get_value_details(other_attribute)
            same_rule.add_param(other_value_details)

        return ruleset
