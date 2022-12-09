from unittest import TextTestRunner, TestSuite, TestLoader
from tests.test_integer_rule import TestIntegerRule
from tests.test_string_rule import TestStringRule
from tests.test_list_rule import TestListRule


test_cases = [
    # TestStringRule,
    # TestIntegerRule,
    TestListRule,
]


def load_tests() -> TestSuite:
    loader = TestLoader()
    suite = TestSuite()

    for _test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(_test_case))

    return suite


if __name__ == '__main__':
    runner = TextTestRunner()
    runner.run(load_tests())
