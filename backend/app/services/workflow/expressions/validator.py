
from typing import List

from .evaluator import validate_expression_syntax


class ExpressionValidator:


    def validate(self, expression: str) -> List[str]:
        return validate_expression_syntax(expression)


def validate_expression(expression: str) -> List[str]:
    validator = ExpressionValidator()
    return validator.validate(expression)

