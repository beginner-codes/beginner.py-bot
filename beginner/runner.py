from io import StringIO
import ast
import base64
import contextlib
import inspect
import sys
import traceback
import resource
import signal


class CPUTimeExceeded(Exception):
    ...


class Executer:
    def __init__(self, name_whitelist, dunder_whitelist, import_whitelist):
        self.name_whitelist = name_whitelist
        self.dunder_whitelist = dunder_whitelist
        self.import_whitelist = import_whitelist

        self.globals = {"__name__": "__main__"}
        self.locals = {}
        self.stdout = StringIO()

        self.exception = False

        signal.signal(signal.SIGXCPU, self.cpu_time_exceeded)

    def cpu_time_exceeded(self, signo, frame):
        raise CPUTimeExceeded()

    def dunder_attributes(self, code_tree):
        attributes = set()
        for node in ast.walk(code_tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                attributes.add(node.attr)
        return attributes

    def generate_builtins(self):
        builtins = {
            name: getattr(__builtins__, name)
            for name in dir(__builtins__)
            if name in self.name_whitelist
        }
        if "print" in builtins:
            builtins["print"] = self.print
        if "getattr" in builtins:
            builtins["getattr"] = self.getattr
        if "__import__" in builtins:
            builtins["__import__"] = self.importer
        return builtins

    def generate_globals(self):
        runtime_globals = self.globals.copy()
        runtime_globals["__builtins__"] = self.generate_builtins()
        return runtime_globals

    def generate_locals(self):
        return self.locals.copy()

    def getattr(self, name, *args, **kwargs):
        if name not in self.name_whitelist | self.dunder_whitelist:
            raise NameError(f"'{name}' is not a whitelisted name")
        return getattr(name, *args, **kwargs)

    def imported_module_parser(self, name):
        return name.split(".")[0]

    def importer(self, name, *args, **kwargs):
        if self.imported_module_parser(name) not in self.import_whitelist:
            raise ImportError(f"Module is not whitelisted: {name}")
        return __import__(name, *args, **kwargs)

    def print(self, *args, **kwargs):
        if "file" not in kwargs:
            kwargs["file"] = self.stdout
        print(*args, **kwargs)

    def run(self, code):
        exceptions = []

        with self.set_recursion_depth(50):
            code_tree = ast.parse(code, "<string>", "exec")

            dunder_attributes = self.dunder_attributes(code_tree)
            if dunder_attributes - self.dunder_whitelist:
                prohibited_attributes = ", ".join(sorted(dunder_attributes - self.dunder_whitelist))
                exceptions.append(f"NameError: These attributes are not whitelisted: {prohibited_attributes}")

            if not exceptions:
                code_object = compile(code_tree, "<string>", "exec")
                try:
                    ns_globals = self.generate_globals()
                    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                    soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
                    resource.setrlimit(resource.RLIMIT_AS, (1000, 1000))
                    resource.setrlimit(resource.RLIMIT_CPU, (1, hard))
                    exec(code_object, ns_globals, ns_globals)
                except MemoryError:
                    exceptions.append("MemoryError: Exceeded process memory limits")
                except CPUTimeExceeded:
                    exceptions.append("Beginnerpy.CPUTimeError: Exceeded process CPU time limits")
                except Exception as ex:
                    err = StringIO()
                    traceback.print_exc(limit=-1, file=err)
                    exceptions.append(err.getvalue())
                    err.close()
                except SystemExit as se:
                    exceptions.append(f"EXIT WITH CODE {0 if se.code is None else se.code}")

        out = self.stdout.getvalue()
        self.stdout.close()
        return out, exceptions

    @contextlib.contextmanager
    def set_recursion_depth(self, depth):
        old_depth = sys.getrecursionlimit()
        sys.setrecursionlimit(depth + len(inspect.stack(0)))
        yield
        sys.setrecursionlimit(old_depth)


if __name__ == "__main__":
    code = base64.b64decode(input().encode()).strip()
    executer = Executer(
        {
            "__import__", "__build_class__",
            "ArithmeticError", "AssertionError", "AttributeError", "BlockingIOError", "BrokenPipeError", "BufferError",
            "BytesWarning", "ChildProcessError", "ConnectionAbortedError", "ConnectionError", "ConnectionRefusedError",
            "ConnectionResetError", "DeprecationWarning", "EOFError", "BaseException", "Exception", "Ellipsis", "False",
            "GeneratorExit", "KeyboardInterrupt", "None", "NotImplemented", "SystemExit", "True", "abs", "all", "any",
            "ascii", "bin", "bool", "bytearray", "bytes", "callable", "chr", "classmethod", "complex", "copyright",
            "credits", "delattr", "dict", "dir", "divmod", "enumerate", "exit", "filter", "float", "format",
            "frozenset", "getattr", "globals", "hasattr", "hash", "hex", "id", "int", "isinstance",
            "issubclass", "iter", "len", "license", "list", "locals", "map", "max", "min", "next", "object", "oct",
            "ord", "pow", "print", "property", "quit", "range", "repr", "reversed", "round", "set", "setattr", "slice",
            "sorted", "staticmethod", "str", "sum", "super", "tuple", "type", "vars", "zip",
        },
        {
            "__name__", "__doc__", "__next__", "__init__", "__new__", "__call__", "__iter__", "__slots__"
        },
        {
            "datetime", "itertools", "functools", "re", "math", "random", "decimal", "string", "textwrap",
            "unicodedata", "stringprep", "struct", "calendar", "collections", "heapq", "bisect", "array", "weakref",
            "types", "copy", "pprint", "reprlib", "enum", "numbers", "cmath", "fractions", "statistics", "operator",
            "pickle", "copyreg", "hashlib", "hmac", "secrets", "time", "json", "base64", "binascii", "typing",
            "dectest", "unittest", "dataclasses", "contextlib", "abc",

        }
    )
    out, exceptions = executer.run(code)
    print(base64.b64encode(out.encode()).decode())
    for exception in exceptions:
        print(base64.b64encode(exception.encode()).decode())
