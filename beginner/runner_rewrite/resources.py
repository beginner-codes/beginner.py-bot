from dataclasses import dataclass, field
from typing import Tuple
import resource
import signal


@dataclass
class RunnerResourceLimits:
    max_memory: int = field(default=1000)
    max_cpu_time: int = field(default=1)
    max_runtime: int = field(default=2)
    exception: str = field(default="")

    _old_as_limit: Tuple[int, int] = field(default=(0, 0))
    _old_cpu_limit: Tuple[int, int] = field(default=(0, 0))

    def __enter__(self):
        signal.signal(signal.SIGXCPU, self.cpu_time_exceeded)
        signal.signal(signal.SIGALRM, self.script_timed_out)

        self._old_as_limit = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (self.max_memory, self._old_as_limit[1]))

        self._old_cpu_limit = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(
            resource.RLIMIT_CPU, (self.max_cpu_time, self._old_cpu_limit[1])
        )

        signal.alarm(self.max_runtime)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)

        resource.setrlimit(resource.RLIMIT_CPU, self._old_cpu_limit)
        resource.setrlimit(resource.RLIMIT_AS, self._old_as_limit)

        if exc_type in {CPUTimeExceeded, ScriptTimedOut, MemoryError}:
            self.exception = f"{exc_type.__name__}: {exc_val}"
            return True

        return False

    def cpu_time_exceeded(self, signo, frame):
        raise CPUTimeExceeded(
            f"Your script exceeded the limits on CPU usage time ({self.max_cpu_time} seconds)"
        )

    def script_timed_out(self, signo, frame):
        raise ScriptTimedOut(
            f"Your script exceeded the maximum allowed run time ({self.max_runtime} seconds)"
        )


class CPUTimeExceeded(Exception):
    ...


class ScriptTimedOut(Exception):
    ...
