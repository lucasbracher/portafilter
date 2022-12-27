from collections import OrderedDict
from abc import ABC, abstractmethod
from typing import Any, Tuple, List, Union, Callable
from portafilter.enums import ValueType
from portafilter.exceptions import InvalidRule, InvalidRuleParam, ValidationError
from portafilter.sandglass import Sandglass, InvalidDate, ParseSpecialKey
from portafilter.utils import trans
from re import match as regex_match
from numbers import Number
from inspect import isclass


class Rule(ABC):

    def __init__(self, *args, **kwargs):
        """The init method.
        """
        self._params = list(args)
        self._metadata = {
            'value_type': None,
        }

    def get_params(self) -> List[Any]:
        """Get the rule params

        Returns:
            List[Any]
        """
        return self._params

    def add_param(self, value: Any) -> None:
        """Add a rule parameter

        Arguments:
            value (Any) -- The rule parameter.
        """
        self._params.append(value)

    def set_metadata(self, key: Union[str, List[Tuple[str, Any]]], value: Any = None) -> None:
        """Set the metadata.

        Arguments:
            key (Union[str, List[Tuple[str, Any]]])

        Keyword Arguments:
            value (Any) -- (default None)
        """
        if isinstance(key, list):
            for _key, _value in key:
                self._metadata[_key] = _value

        else:
            self._metadata[key] = value

    def unset_metadata(self, key: Union[str, List[str]]) -> None:
        """Set the metadata.

        Arguments:
            key (Union[str, List[str]])
        """
        if isinstance(key, list):

            for _key in key:
                if _key in self._metadata:
                    del self._metadata[_key]
        else:

            if key in self._metadata:
                del self._metadata[key]

    def get_metadata(self, key: str) -> Any:
        """Get the metadata.

        Arguments:
            key {str}

        Returns:
            Any
        """
        return self._metadata.get(key)

    def get_value_type(self) -> ValueType:
        """Get the value type.

        Returns:
            ValueType
        """
        return self.get_metadata('value_type')

    def is_required(self) -> bool:
        """The is required check

        Returns:
            bool
        """
        return self.get_metadata('required')

    def is_nullable(self) -> bool:
        """The is nullable check

        Returns:
            bool
        """
        return self.get_metadata('nullable')

    def is_skippable(self) -> bool:
        """Skip the rule check

        Returns:
            bool
        """
        return self.get_metadata('value') is None and (self.is_nullable() or not self.is_required())

    @abstractmethod
    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        pass

    @abstractmethod
    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        pass


class RequiredRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        if isinstance(value, Number) or isinstance(value, bool):
            return True

        else:
            return (self.is_nullable() and value is None) or (True if value else False)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.required', attributes={'attribute': attribute})


class NullableRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return True

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return ''


class StringRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return isinstance(value, str)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.string', attributes={'attribute': attribute})


class MinRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool

        Raises:
            NotImplementedError
            InvalidRuleParam
        """
        value_type = self.get_value_type()

        try:
            min_value = float(params[0])

        except InvalidRuleParam as e:
            raise e

        if value_type == ValueType.STRING:
            return isinstance(value, str) and len(value) >= min_value

        elif value_type == ValueType.LIST:
            return isinstance(value, list) and len(value) >= min_value

        elif value_type in [ValueType.NUMERIC, ValueType.INTEGER]:
            return isinstance(value, int) and value >= min_value

        else:
            raise NotImplementedError

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        value_type = self.get_value_type()

        if value_type == ValueType.STRING:
            message_key = 'en.min.string'

        elif value_type == ValueType.LIST:
            message_key = 'en.min.list'

        elif value_type in [ValueType.NUMERIC, ValueType.INTEGER]:
            message_key = 'en.min.numeric'

        else:
            raise NotImplementedError

        return trans(message_key, attributes={'attribute': attribute, 'min': params[0]})


class MaxRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool

        Raises:
            NotImplementedError
            InvalidRuleParam
        """
        value_type = self.get_value_type()

        try:
            max_value = float(params[0])

        except InvalidRuleParam as e:
            raise e

        if value_type == ValueType.STRING:
            return isinstance(value, str) and len(value) <= max_value

        elif value_type == ValueType.LIST:
            return isinstance(value, list) and len(value) <= max_value

        elif value_type in [ValueType.NUMERIC, ValueType.INTEGER]:
            return isinstance(value, int) and value <= max_value

        else:
            raise NotImplementedError

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        value_type = self.get_value_type()

        if value_type == ValueType.STRING:
            message_key = 'en.max.string'

        elif value_type == ValueType.LIST:
            message_key = 'en.max.list'

        elif value_type in [ValueType.NUMERIC, ValueType.INTEGER]:
            message_key = 'en.max.numeric'

        else:
            raise NotImplementedError

        return trans(message_key, attributes={'attribute': attribute, 'max': params[0]})


class IntegerRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return isinstance(value, int)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.integer', attributes={'attribute': attribute})


class NumericRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return isinstance(value, Number)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.numeric', attributes={'attribute': attribute})


class BooleanRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return isinstance(value, bool)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.boolean', attributes={'attribute': attribute})


class InRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return value in params

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.in', attributes={'attribute': attribute})


class NotInRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return value not in params

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.not_in', attributes={'attribute': attribute})


class SameRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        other_value, other_value_exists = params[1]
        return value == other_value

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.same', attributes={'attribute': attribute, 'other': params[0]})


class EmailRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        return regex_match(regex, value or '')

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.email', attributes={'attribute': attribute})


class ListRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        result = isinstance(value, list)

        if result and params and value:

            list_item_type = ValueType(params[0])

            for list_item in value:

                if list_item_type == ValueType.DICT:

                    if not isinstance(list_item, dict):
                        return False

                elif list_item_type == ValueType.STRING:

                    if not isinstance(list_item, str):
                        return False

                elif list_item_type == ValueType.INTEGER:

                    if not isinstance(list_item, int):
                        return False

                elif list_item_type == ValueType.NUMERIC:

                    if not isinstance(list_item, Number):
                        return False

                else:
                    raise NotImplementedError

        return result

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        _key = None
        _attributes = {'attribute': attribute}

        if params:
            _key = 'list_item_type'
            _attributes['type'] = params[0]

        else:
            _key = 'list'

        return trans(f'en.{_key}', attributes=_attributes)


class DictRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        return isinstance(value, dict)

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            str
        """
        return trans('en.dict', attributes={'attribute': attribute})


class DateRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        # Rejecting the Sandglass parsing special keys for the date rule.
        if Sandglass.is_parse_special_key(value):
            return False

        try:
            Sandglass(value, date_format=None if not params else ','.join(params))

            return True

        except Exception as e:
            return False

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.date', attributes={'attribute': attribute}) if not params else \
            trans('en.date_format', attributes={'attribute': attribute, 'format': ','.join(params)})


class AfterRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        # Rejecting the Sandglass parsing special keys for the date rule.
        if Sandglass.is_parse_special_key(value):
            return False

        try:
            return Sandglass(value).start_of_day() > Sandglass(params[0]).start_of_day()

        except Exception as e:
            return False

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.after', attributes={'attribute': attribute, 'date': params[0]})


class AfterOrEqualRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        # Rejecting the Sandglass parsing special keys for the date rule.
        if Sandglass.is_parse_special_key(value):
            return False

        try:
            return Sandglass(value).start_of_day() >= Sandglass(params[0]).start_of_day()

        except Exception as e:
            return False

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.after_or_equal', attributes={'attribute': attribute, 'date': params[0]})


class BeforeRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        # Rejecting the Sandglass parsing special keys for the date rule.
        if Sandglass.is_parse_special_key(value):
            return False

        try:
            return Sandglass(value).start_of_day() < Sandglass(params[0]).start_of_day()

        except Exception as e:
            return False

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.before', attributes={'attribute': attribute, 'date': params[0]})


class BeforeOrEqualRule(Rule):

    def passes(self, attribute: str, value: Any, params: List[Any]) -> bool:
        """Determine if the validation rule passes.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            bool
        """
        # Rejecting the Sandglass parsing special keys for the date rule.
        if Sandglass.is_parse_special_key(value):
            return False

        try:
            return Sandglass(value).start_of_day() <= Sandglass(params[0]).start_of_day()

        except Exception as e:
            return False

    def message(self, attribute: str, value: Any, params: List[Any]) -> str:
        """The validation error message.

        Arguments:
            attribute {str}
            value {Any}
            params {List[Any]}

        Returns:
            strp
        """
        return trans('en.before_or_equal', attributes={'attribute': attribute, 'date': params[0]})


class Ruleset:

    # Static variable for the custom ruleset.
    rules = None

    def __init__(self, rules: Union[str, List[Union[Rule, str]]]):
        """The init method

        Arguments:
            rules {Union[str, List[Union[Rule, str]]]}
        """
        self._rules = self._parse(rules)
        self._set_rules_metadata()
        self._errors = []

    def _parse(self, rules: Union[str, List[Union[Rule, str]]]) -> OrderedDict:
        """Parse the rules

        Arguments:
            rules {Union[str, List[Union[Rule, str]]]}
        
        Returns:
            OrderedDict
        """
        parsed_rules = OrderedDict()

        rules_list = rules if isinstance(rules, list) else rules.split('|')

        for _rule in rules_list:
            if isinstance(_rule, str):
                _rule_params = _rule.split(':')
                _rule_name = _rule_params.pop(0)
                _rule_params = self._split_rule_params(':'.join(_rule_params))

                rule_class = globals().get(f"{''.join([_.capitalize() for _ in _rule_name.split('_')])}Rule")

                if rule_class:
                    parsed_rules[_rule_name] = rule_class(*_rule_params)

                else:
                    raise InvalidRule(f"Invalid rule: {_rule_name}")

            elif isinstance(_rule, object):

                if isclass(_rule):

                    if issubclass(_rule, Rule) and isinstance(_rule, Callable):
                        parsed_rules[_rule.__name__] = _rule()

                    elif issubclass(_rule, Ruleset) and isinstance(_rule, Callable):
                        _rule_instance = _rule(_rule.rules)
                        for _ruleset_rule_name, _ruleset_rule_class in _rule_instance.get_rules().items():
                            parsed_rules[_ruleset_rule_name] = _ruleset_rule_class

                else:
                    parsed_rules[_rule.__class__.__name__] = _rule

        return parsed_rules

    def get_rule(self, rule_name: str) -> Union[Rule, None]:
        """Get the specified rule

        Arguments:
            rule_name {str}

        Returns:
            Union[Rule, None]
        """
        return self._rules.get(rule_name)

    def get_rules(self) -> OrderedDict:
        """Get the rules

        Returns:
            OrderedDict
        """
        return self._rules

    def has_rule(self, rule_name: str) -> bool:
        """Has the specified rule

        Arguments:
            rule_name {str}

        Returns:
            bool
        """
        return rule_name in self._rules

    @staticmethod
    def _split_rule_params(rule_params: str) -> List[str]:
        """Split the rule params

        Arguments:
            rule_params {str}

        Returns:
            List[str]
        """
        return rule_params.split(',') if rule_params else []

    def get_value_type(self) -> ValueType:
        """Get the value type based on the rules

        Returns:
            ValueType
        """
        value_type = ValueType.STRING

        for rule_name in self._rules.keys():
            try:
                value_type = ValueType(rule_name)
                break

            except ValueError as e:
                pass

        return value_type

    def _set_rules_metadata(self) -> None:
        """Set the rules metadata.
        """
        value_type = self.get_value_type()
        is_required = 'required' in self._rules
        is_nullable = 'nullable' in self._rules
        for rule_name, rule in self._rules.items():
            rule.set_metadata([
                ('value_type', value_type),
                ('required', is_required),
                ('nullable', is_nullable),
            ])

    def validate(self, attribute: str, value: Any, value_exists: bool = True) -> None:
        """Validate the ruleset

        Arguments:
            attribute {str}
            value {Any}

        Keyword Arguments:
            value_exists {bool} -- The value exists in the main data (default: {True})

        Raises:
            ValidationError
        """
        for rule_name, rule in self._rules.items():

            # Adding the temporary metadata
            rule.set_metadata([('value_exists', value_exists), ('value', value)])

            if not rule.is_skippable() and not rule.passes(attribute, value, rule.get_params()):

                self._errors.append(rule.message(attribute, value, rule.get_params()))

            # Removing the temporary metadata
            rule.unset_metadata(['value_exists', 'value'])

        if self.has_error():
            raise ValidationError

    def has_error(self) -> bool:
        """Check the failure status.

        Returns:
            bool
        """
        return True if self._errors else False

    def errors(self) -> list:
        """Get the error messages list.

        Returns:
            list
        """
        return self._errors


class RuleList:

    def __init__(self, rules: dict):
        """The init method

        Arguments:
            rules {dict}
        """
        self._rules = self._parse(rules)

    @staticmethod
    def _parse(rules: dict) -> OrderedDict:
        """Parse the rules

        Returns:
            OrderedDict

        Raises:
            Exception -- Invalid rule type.
        """
        parsed_rules = OrderedDict()

        for attribute, _rules in rules.items():

            if isinstance(_rules, str) or isinstance(_rules, list):
                parsed_rules[attribute] = Ruleset(_rules)

            elif isclass(_rules) and isinstance(_rules, Callable) and issubclass(_rules, Ruleset):

                parsed_rules[attribute] = _rules(_rules.rules)

            else:
                raise Exception('Invalid rule type in parsing rules.')

        return parsed_rules

    def __iter__(self):
        """The iter magic method
        """
        self._iter_current_index = 0
        self._iter_fields = list(self._rules.keys())
        self._iter_fields_count = len(self._iter_fields)
        return self

    def __next__(self) -> Tuple[str, Ruleset]:
        """The next magic method

        Returns:
            Tuple[str, OrderedDict]

        Raises:
            StopIteration
        """
        if self._iter_current_index < self._iter_fields_count:
            attribute = self._iter_fields[self._iter_current_index]
            self._iter_current_index += 1
            return attribute, self._rules[attribute]

        raise StopIteration
