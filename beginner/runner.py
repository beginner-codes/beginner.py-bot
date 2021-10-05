import ast
import contextlib
import inspect
import io
import json
import pathlib
import resource
import signal
import sys
import time
import traceback
import uuid
import hashlib


class Numpy:
    def __init__(self):
        self.__numpy = __import__("numpy")

    def __getattr__(self, item):
        if item in {"load", "save", "savetxt"}:
            raise AttributeError(f"numpy.{item} is disabled")
        return getattr(self.__numpy, item)

    def __repr__(self):
        return repr(self.__numpy)

    def __str__(self):
        return str(self.__numpy)

    def __dir__(self):
        return dir(self.__numpy)


class Pickle:
    def __init__(self):
        self.__pickles = {}
        self.__pickle = __import__("pickle")

    def __getattr__(self, item):
        raise AttributeError(f"pickle.{item} is disabled")

    def __repr__(self):
        return repr(self.__pickle)

    def __str__(self):
        return str(self.__pickle)

    def __dir__(self):
        return dir(self.__pickle)

    def load(self, file, *_, **__):
        unique_id = file.read()
        if unique_id not in self.__pickles:
            raise RuntimeError("Unknown pickle detected")

        return self.__pickles[unique_id]

    def loads(self, unique_id, *_, **__):
        if unique_id not in self.__pickles:
            raise RuntimeError("Unknown pickle detected")

        return self.__pickles[unique_id]

    def dump(self, obj, file, *_, **__):
        unique_id = hashlib.md5(uuid.uuid4().bytes)
        self.__pickles[unique_id] = obj
        file.write(unique_id)

    def dumps(self, obj, *_, **__):
        unique_id = hashlib.md5(uuid.uuid4().bytes)
        self.__pickles[unique_id] = obj
        return unique_id


class CPUTimeExceeded(Exception):
    ...


class ScriptTimedOut(Exception):
    ...


class Executer:
    def __init__(self, name_whitelist, dunder_whitelist, import_whitelist):
        self.name_whitelist = name_whitelist
        self.dunder_whitelist = dunder_whitelist
        self.import_whitelist = import_whitelist

        self.globals = {"__name__": "__main__"}
        self.locals = {}
        self.stdin = io.StringIO()

        self.exception = False

        signal.signal(signal.SIGXCPU, self.cpu_time_exceeded)
        signal.signal(signal.SIGALRM, self.script_timed_out)

    def cpu_time_exceeded(self, signo, frame):
        raise CPUTimeExceeded()

    def script_timed_out(self, signo, frame):
        raise ScriptTimedOut()

    def dunder_attributes(self, code_tree):
        attributes = set()
        for node in ast.walk(code_tree):
            if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                attributes.add(node.attr)
        return attributes

    def generate_builtins(self, restricted=True):
        b = __builtins__
        if not isinstance(b, dict):
            b = {name: getattr(b, name) for name in dir(b)}
        builtins = {
            name: b[name] for name in b if name in self.name_whitelist or not restricted
        }
        if "input" in builtins:
            builtins["input"] = self.input
        if restricted:
            if "getattr" in builtins:
                builtins["getattr"] = self.getattr
            if "exec" in builtins:
                builtins["exec"] = lambda *a, **k: self.exec(*a, runner=exec, **k)
            if "eval" in builtins:
                builtins["eval"] = lambda *a, **k: self.exec(*a, runner=eval, **k)
        if "__import__" in builtins:
            builtins["__import__"] = (
                self.importer
                if restricted
                else self.admin_importer
            )
        builtins["getsizeof"] = sys.getsizeof
        return builtins

    def generate_globals(self, restricted=True):
        runtime_globals = self.globals.copy()
        runtime_globals["__builtins__"] = self.generate_builtins(restricted)
        return runtime_globals

    def generate_locals(self):
        return self.locals.copy()

    def getattr(self, obj, name, *args, **kwargs):
        if name not in self.name_whitelist | self.dunder_whitelist:
            raise NameError(f"'{name}' is not a whitelisted name")
        return getattr(obj, name, *args, **kwargs)

    def imported_module_parser(self, name):
        return name.split(".")[0]

    def importer(self, name, *args, **kwargs):
        if self.imported_module_parser(name) not in self.import_whitelist:
            raise ImportError(f"Module is not whitelisted: {name}")
        if name == "numpy":
            return Numpy()
        if name == "pickle":
            return Pickle()
        return __import__(name, *args, **kwargs)

    def admin_importer(self, name, *args, **kwargs):
        if name in {"pickle"}:
            return self.importer(name, *args, **kwargs)

        return __import__(name, *args, **kwargs)

    def input(self, prompt="", **kwargs):
        print(prompt, end="")
        if len(self.stdin.getvalue()) == self.stdin.tell():
            raise EOFError("Nothing left to read from stdin")

        line = self.stdin.readline().rstrip("\n")
        print(line)
        return line

    def exec(self, code, runner=exec, restricted=True):
        try:
            code_tree = ast.parse(code, "<string>", runner.__name__)
        except SyntaxError as excp:
            msg, (file, line_no, column, line) = excp.args
            spaces = " " * (column - 1)
            sys.stderr.write(
                f"Line {line_no}\n{line.rstrip() if line else ''}\n{spaces}^\nSyntaxError: {msg}"
            )
            exceptions = True
        else:
            dunder_attributes = self.dunder_attributes(code_tree)
            if restricted and dunder_attributes - self.dunder_whitelist:
                prohibited_attributes = ", ".join(
                    sorted(dunder_attributes - self.dunder_whitelist)
                )
                raise NameError(
                    f"These attributes are not whitelisted: {prohibited_attributes}"
                )

            code_object = compile(code_tree, "<string>", runner.__name__)
            ns_globals = self.generate_globals(restricted)
            result = runner(code_object, ns_globals, ns_globals)
            if runner == eval:
                print(repr(result))

            return result

    def run(self, code, user_input, runner=exec, docs=False, restricted=True):
        self.stdin = io.StringIO(user_input)
        exceptions = False

        with self.set_recursion_depth(100):
            try:
                code_tree = ast.parse(code, "<string>", runner.__name__)
            except SyntaxError as excp:
                msg, (file, line_no, column, line) = excp.args
                spaces = " " * (column - 1)
                sys.stderr.write(
                    f"Line {line_no}\n{line.rstrip() if line else ''}\n{spaces}^\nSyntaxError: {msg}"
                )
                exceptions = True
            else:
                dunder_attributes = self.dunder_attributes(code_tree)
                if restricted and dunder_attributes - self.dunder_whitelist:
                    prohibited_attributes = ", ".join(
                        sorted(dunder_attributes - self.dunder_whitelist)
                    )
                    sys.stderr.write(
                        f"NameError: These attributes are not whitelisted: {prohibited_attributes}"
                    )
                    exceptions = True

                if not exceptions:
                    code_object = compile(code_tree, "<string>", runner.__name__)
                    try:
                        ns_globals = self.generate_globals(restricted)
                        _, hard = resource.getrlimit(resource.RLIMIT_CPU)
                        resource.setrlimit(resource.RLIMIT_CPU, (2, hard))
                        signal.alarm(2)
                        start = time.time_ns()
                        result = runner(code_object, ns_globals, ns_globals)
                        signal.alarm(0)
                        if runner == eval:
                            if docs:
                                print(
                                    result.__doc__
                                    if hasattr(result, "__doc__")
                                    and result.__doc__.strip()
                                    else "NO DOCS"
                                )
                            else:
                                print(repr(result))
                    except MemoryError:
                        sys.stderr.write("MemoryError: Exceeded process memory limits")
                    except CPUTimeExceeded:
                        sys.stderr.write(
                            "Beginnerpy.CPUTimeError: Exceeded process CPU time limits"
                        )
                    except ScriptTimedOut:
                        sys.stderr.write(
                            "Beginnerpy.ScriptTimedOut: Script took too long to complete"
                        )
                    except ImportError as ex:
                        sys.stderr.write(f"ImportError: {ex.args[0]}")
                    except Exception as ex:
                        traceback.print_exc(limit=-1)
                    except SystemExit as se:
                        sys.stderr.write(
                            f"EXIT WITH CODE {0 if se.code is None else se.code}\n"
                        )
                    finally:
                        print(f"\n^^^^{time.time_ns() - start}^^^^")

    @contextlib.contextmanager
    def set_recursion_depth(self, depth):
        old_depth = sys.getrecursionlimit()
        sys.setrecursionlimit(depth + len(inspect.stack(0)))
        yield
        sys.setrecursionlimit(old_depth)


if __name__ == "__main__":
    with (
        pathlib.Path(__file__).parent / "allowed_modules.txt"
    ).open() as allowed_modules_file:
        allowed_modules = list(
            line.strip() for line in allowed_modules_file.readlines() if line.strip()
        )

    executer = Executer(
        {
            "__import__",
            "__build_class__",
            "ArithmeticError",
            "AssertionError",
            "AttributeError",
            "BlockingIOError",
            "BrokenPipeError",
            "BufferError",
            "BytesWarning",
            "ChildProcessError",
            "ConnectionAbortedError",
            "ConnectionError",
            "ConnectionRefusedError",
            "ConnectionResetError",
            "DeprecationWarning",
            "EOFError",
            "BaseException",
            "Exception",
            "Ellipsis",
            "False",
            "GeneratorExit",
            "KeyboardInterrupt",
            "None",
            "NotImplemented",
            "SystemExit",
            "True",
            "abs",
            "all",
            "any",
            "ascii",
            "bin",
            "bool",
            "bytearray",
            "bytes",
            "callable",
            "chr",
            "classmethod",
            "complex",
            "copyright",
            "credits",
            "delattr",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "eval",
            "exec",
            "exit",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "globals",
            "hasattr",
            "hash",
            "hex",
            "id",
            "input",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "license",
            "list",
            "locals",
            "map",
            "max",
            "min",
            "NameError",
            "next",
            "object",
            "oct",
            "ord",
            "pow",
            "print",
            "property",
            "quit",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "TypeError",
            "ValueError",
            "vars",
            "zip",
        },
        {
            "__name__",
            "__doc__",
            "__next__",
            "__init__",
            "__new__",
            "__call__",
            "__iter__",
            "__slots__",
            "__class__",
            "__dict__",
            "__await__",
        },
        allowed_modules,
    )
    data = json.loads(sys.stdin.read(-1))
    runners = {"eval": eval, "exec": exec, "docs": eval}
    arg = len(sys.argv) < 2 or sys.argv[1]
    runner = runners.get(arg, exec)
    executer.run(
        data["code"], data["input"], runner, arg == "docs", data.get("restricted", True)
    )
