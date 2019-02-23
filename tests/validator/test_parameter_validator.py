from tests.base import TestCase, main
from ocrd_validators import ParameterValidator

class TestParameterValidator(TestCase):

    def test_default_assignment(self):
        validator = ParameterValidator({
            "parameters": {
                "num-param": {
                    "type": "number",
                    "default": 1
                },
                "baz": {
                    "type": "string",
                    "required": True,
                },
                'foo': {
                    "required": False
                }
            }
        })
        obj = {'baz': '23'}
        report = validator.validate(obj)
        self.assertTrue(report.is_valid)
        self.assertEqual(obj, {'baz': '23', "num-param": 1})


if __name__ == '__main__':
    main()