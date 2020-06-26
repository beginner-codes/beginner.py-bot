from beginner.runner.buffer import RunnerOutputBuffer
from beginner.runner.builtins import RunnerBuiltins
from beginner.runner.config import RunnerConfig
from beginner.runner.resources import RunnerResourceLimits
from beginner.runner.scanner import Scanner
from beginner.runner.module_wrapper import RunnerAttributeError, RunnerImportError
from typing import Any, Dict, Set
import ast
import bevy
import io
import pathlib
import traceback


class Runner(bevy.Bevy):
    buffer: RunnerOutputBuffer
    builtins: RunnerBuiltins
    config: RunnerConfig

    def __init__(self, code: str, mode: str):
        self._code = code
        self._mode = mode
        self._config_path = pathlib.Path(__file__).parent.parent / "config"

        self.output = ""
        self.exception = ""
        self.exit_code = 0

    def run(self):
        try:
            tree = ast.parse(self._code, "<discord>", self._mode)
        except SyntaxError as exc:
            msg, (file, line_no, column, line) = exc.args
            spaces = " " * (column - 2)
            self.exception = f"File \"{file}\", line {line_no}\n{line.rstrip()}\n{spaces}^\nSyntaxError: {msg}"
            return

        scanner = Scanner(tree)
        disabled_attributes = self.disabled_dunder_attributes(scanner)
        if disabled_attributes:
            self.exception = f"AttributeError: Found disabled attributes ({', '.join(sorted(disabled_attributes))})"
            return

        self.preload_modules(scanner)

        global_ns = self.build_globals()
        limits = None
        try:
            code = compile(tree, "<discord>", self._mode)
            with RunnerResourceLimits() as limits:
                if self._mode == "exec":
                    exec(code, global_ns, global_ns)
                elif self._mode == "eval":
                    self.buffer.writelines(
                        repr(
                            eval(code, global_ns, global_ns)
                        )
                    )
        except RunnerAttributeError as exc:
            self.exception = f"AttributeError: {exc.args[0]}"
        except RunnerImportError as exc:
            self.exception = f"ImportError: {exc.args[0]}"
        except SystemExit as se:
            self.exit_code = 0 if se.code is None else se.code
        except Exception as exc:
            err = io.StringIO()
            traceback.print_exc(limit=-1, file=err)
            self.exception = err.getvalue()
            err.close()

        if limits and limits.exception:
            self.exception = limits.exception

        self.output = self.buffer.getvalue()
        self.buffer.close()

    def build_globals(self) -> Dict[str, Any]:
        return {
            "__name__": "__main__",
            "__builtins__": self.builtins.get_builtins()
        }

    def disabled_dunder_attributes(self, scanner: Scanner) -> Set[str]:
        attrs = scanner.get_dunder_attributes()
        enabled_attributes = set(self.config.get("enabled_special_attributes"))
        return attrs - enabled_attributes

    def preload_modules(self, scanner: Scanner):
        """ Preload modules since some will fail to load once resource limits are put in place. """
        for module in scanner.get_imports():
            try:
                __import__(module)
            except ImportError:
                return  # We don't care, this exception will be raised when the code is run, so just stop


if __name__ == "__main__":
    code = """1"""
    run = (
        Runner
            .context(RunnerConfig(pathlib.Path(__file__).parent.parent / "config"))
            .build(code, "eval")
    )
    run.run()
    if run.output:
        out = run.output.rstrip().replace("\n", "\n>>> ")
        print(f">>> {out}")
    if run.exception:
        print(run.exception)

    code = """import os
import types
os.__getattr__ = types.MethodType(lambda self, name: super().__getattribute__(name), os)
print(os.__str__())"""
    run = (
        Runner
            .context(RunnerConfig(pathlib.Path(__file__).parent.parent / "config"))
            .build(code, "exec")
    )
    run.run()
    if run.output:
        out = run.output.rstrip().replace("\n", "\n>>> ")
        print(f">>> {out}")
    else:
        print("--- NO OUTPUT ---")
    if run.exception:
        print(run.exception)
    if run.exit_code != 0:
        print(f"EXITED WITH CODE {run.exit_code}")
