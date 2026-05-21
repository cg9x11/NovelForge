
from __future__ import annotations
from app.locales import schema_field_description

import inspect
from typing import Any, AsyncIterator

from pydantic import BaseModel, Field

from app.services.workflow.expressions import evaluate_expression
from app.services.workflow.expressions.builtins import get_safe_builtins
from app.services.workflow.expressions.functions import get_builtin_functions, get_helper_metadata
from app.services.workflow.nodes.base import BaseNode
from app.services.workflow.registry import register_node


class ExpressionInput(BaseModel):


    expression: str = Field(
        ...,
        description=schema_field_description("expression"),
        json_schema_extra={
            "x-component": "CodeEditor",
            "x-component-props": {
                "language": "python",
                "placeholder": "Expression helper"
            }
        },
    )


class ExpressionOutput(BaseModel):


    result: Any = Field(..., description=schema_field_description("result"))


def _build_helper_docs() -> list[str]:
    helpers = get_builtin_functions()
    helper_meta = get_helper_metadata()
    if not helpers:
        return ["Expression helper"]

    ranked_names = sorted(
        helpers.keys(),
        key=lambda name: (helper_meta.get(name).priority if helper_meta.get(name) else 50, name),
        reverse=True,
    )

    lines: list[str] = ["Expression helper"]
    for name in ranked_names[:3]:
        func = helpers[name]
        signature = str(inspect.signature(func))
        meta = helper_meta.get(name)
        summary = (meta.summary if meta else ((inspect.getdoc(func) or "").splitlines()[0] if inspect.getdoc(func) else "Expression helper")).strip()
        scenario = meta.scenario if meta else "Expression helper"
        example = meta.example if meta else ""
        line = f"- `{name}{signature}`（\u573a\u666f：{scenario}，\u4f18\u5148\u7ea7：{meta.priority if meta else 50}）\n  - \u8bf4\u660e：{summary}"
        if example:
            line += f"\n  - \u793a\u4f8b：`{example}`"
        lines.append(line)

    lines.append("Expression helper")
    for name in ranked_names:
        func = helpers[name]
        signature = str(inspect.signature(func))
        meta = helper_meta.get(name)
        summary = (meta.summary if meta else ((inspect.getdoc(func) or "").splitlines()[0] if inspect.getdoc(func) else "Expression helper")).strip()
        lines.append(f"- `{name}{signature}`：{summary}")
    return lines


def _build_builtin_docs() -> str:
    builtin_names = sorted(get_safe_builtins().keys())
    return ", ".join(f"`{name}`" for name in builtin_names)


def _build_expression_documentation() -> str:
    helper_lines = "\n".join(_build_helper_docs())
    builtin_line = _build_builtin_docs()

    return f"""
\u8868\u8fbe\u5f0f\u8282\u70b9\u7528\u4e8e\u6267\u884c**\u53d7\u63a7 Python \u8868\u8fbe\u5f0f**，\u9002\u5408\u505a\u5b57\u6bb5\u63d0\u53d6、\u5217\u8868\u8f6c\u6362、\u6761\u4ef6\u62fc\u88c5。

1. \u8282\u70b9\u8f93\u51fa\u7ed3\u6784\u56fa\u5b9a\u4e3a `{{"result": <\u8ba1\u7b97\u7ed3\u679c>}}`，\u540e\u7eed\u8282\u70b9\u5fc5\u987b\u901a\u8fc7 `.result` \u8bbf\u95ee。
2. \u53ef\u76f4\u63a5\u8bbf\u95ee\u5de5\u4f5c\u6d41\u4e0a\u4e0b\u6587\u53d8\u91cf（\u5982 `project`、`cards`、`wait_xxx`）。
3. \u63a8\u8350\u4f18\u5148\u4f7f\u7528\u6807\u51c6 Python \u8868\u8fbe\u5f0f\u8bed\u6cd5（\u63a8\u5bfc\u5f0f、\u4e09\u5143\u8868\u8fbe\u5f0f、f-string）。
4. \u5b57\u5178\u652f\u6301\u70b9\u53f7\u8bbf\u95ee（\u5982 `card.content.title`），\u7f3a\u5931\u5b57\u6bb5\u4f1a\u6309\u7a7a\u503c\u5904\u7406。

```python
card.content.items or []
[item for item in items if item.status == "active"]
f"\u5171\u5904\u7406 {{len(items)}} \u9879"
items if wait_ai.count > 0 else []
```

```python
mapped = Logic.Expression(expression="{{item.id: item.name for item in cards}}")
Card.BatchUpsert(items=mapped.result)
```

{builtin_line}

{helper_lines}
""".strip()


@register_node
class ExpressionNode(BaseNode):


    node_type = "Logic.Expression"
    category = "logic"
    label = "Expression"
    description = "Run a safe Python expression and output result"

    input_model = ExpressionInput
    output_model = ExpressionOutput

    @classmethod
    def get_metadata(cls):
        metadata = super().get_metadata()
        metadata.description = cls.description
        metadata.documentation = _build_expression_documentation()
        return metadata

    async def execute(self, input_data: ExpressionInput) -> AsyncIterator[ExpressionOutput]:
        expr_context = self.context.variables

        try:
            result = evaluate_expression(input_data.expression, expr_context)
            yield ExpressionOutput(result=result)
        except Exception as e:
            raise ValueError(
                f"\u8868\u8fbe\u5f0f\u6267\u884c\u5931\u8d25: {str(e)}\n"
                f"\u8868\u8fbe\u5f0f: {input_data.expression}\n"
                f"\u53ef\u7528\u53d8\u91cf: {', '.join(expr_context.keys())}"
            )
