
from dataclasses import dataclass
from typing import List, Dict, Optional, Any


@dataclass
class Statement:
    line_number: int
    variable: str
    node_type: Optional[str]
    config: Dict[str, Any]
    is_async: bool
    depends_on: List[str]
    code: Optional[str] = None
    disabled: bool = False
    description: str = ""

    def __repr__(self):
        return f"Statement(line={self.line_number}, var={self.variable}, type={self.node_type}, disabled={self.disabled})"


@dataclass
class ExecutionPlan:
    statements: List[Statement]
    dependencies: Dict[str, List[str]]

    def get_parallel_groups(self) -> List[List[Statement]]:
        groups = [[stmt] for stmt in self.statements]
        return groups

    def _can_merge_with_last_group(
        self,
        last_group: List[Statement],
        new_stmts: List[Statement]
    ) -> bool:
        last_group_vars = {stmt.variable for stmt in last_group}

        for new_stmt in new_stmts:
            if any(dep in last_group_vars for dep in new_stmt.depends_on):
                return False

        return True

    def validate(self) -> None:
        defined_vars = set()

        for stmt in self.statements:
            for dep in stmt.depends_on:
                if dep not in defined_vars:
                    raise ValueError(
                        f"\u884c {stmt.line_number}: \u53d8\u91cf '{stmt.variable}' "
                        f"\u4f9d\u8d56\u672a\u5b9a\u4e49\u7684\u53d8\u91cf '{dep}'"
                    )

            defined_vars.add(stmt.variable)

        try:
            self.get_parallel_groups()
        except ValueError as e:
            raise ValueError(f"\u6267\u884c\u8ba1\u5212\u9a8c\u8bc1\u5931\u8d25: {e}")
