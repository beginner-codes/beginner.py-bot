import ast
from typing import Set


class Scanner:
    def __init__(self, ast_object: ast.AST):
        self._ast = ast_object

    def get_imports(self) -> Set[str]:
        modules = set()
        for node in ast.walk(self._ast):
            if isinstance(node, ast.Import):
                modules.add(node.names[0].name)
            elif isinstance(node, ast.ImportFrom):
                modules.add(node.module)
            elif (
                isinstance(node, ast.Call)
                and hasattr(node.func, "id")
                and node.func.id == "__import__"
            ):
                modules.add(node.args[0].n)
        return modules

    def get_dunder_attributes(self) -> Set[str]:
        attributes = set()
        for node in ast.walk(self._ast):
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                attributes.add(node.attr)
        return attributes
