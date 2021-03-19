from queue import LifoQueue
from typing import Optional, Tuple
from string import printable


class BrainfuckInterpreter:
    def __init__(self, code: str, data_in: str = ""):
        self._code = code
        self._exception = None
        self._in = data_in
        self._instruction_pointer = 0
        self._out = ""
        self._register_pointer = 0
        self._registers = [0]
        self._stack = LifoQueue()
        self._table = "\n" + printable.replace("\n", "")
        self._generation = 0

    @property
    def register(self):
        return self._registers[self._register_pointer]

    @register.setter
    def register(self, value):
        self._registers[self._register_pointer] = value

    def run(self) -> Tuple[str, Optional[str]]:
        instructions = {
            "[": self._jump_forward,
            "]": self._jump_back,
            ">": self._increment_register_pointer,
            "<": self._decrement_register_pointer,
            "+": self._increment_register,
            "-": self._decrement_register,
            ".": self._print,
            ",": self._read,
        }
        while self._instruction_pointer < len(self._code) and not self._exception:
            if self._generation >= 10000:
                self._exception = "Code took too long to run"
                break

            instruction = self._code[self._instruction_pointer]
            if instruction in instructions:
                self._instruction_pointer = instructions[instruction]()
            else:
                self._instruction_pointer += 1

            self._generation += 1

        return self._out, self._exception

    def _jump_forward(self) -> int:
        if self.register == 0:
            return self._find_next_back_jump() + 1

        self._stack.put(self._instruction_pointer)
        return self._instruction_pointer + 1

    def _jump_back(self) -> int:
        if self.register == 0:
            return self._instruction_pointer + 1

        elif self._stack.empty():
            self._exception = f"No forward jump found before the instruction {self._instruction_pointer}"
            return -1

        return self._stack.get()

    def _increment_register_pointer(self) -> int:
        self._register_pointer += 1
        if self._register_pointer == len(self._registers):
            self._registers.append(0)

        return self._instruction_pointer + 1

    def _decrement_register_pointer(self) -> int:
        if self._register_pointer == 0:
            self._exception = (
                f"Register out of bounds -1 at instruction {self._instruction_pointer}"
            )
            return -1

        self._register_pointer -= 1
        return self._instruction_pointer + 1

    def _increment_register(self) -> int:
        self.register += 1
        return self._instruction_pointer + 1

    def _decrement_register(self) -> int:
        self.register -= 1
        return self._instruction_pointer + 1

    def _print(self) -> int:
        if self.register >= len(self._table):
            self._exception = f"Cannot decode character {self.register} at instruction {self._instruction_pointer}"
            return -1

        self._out += self._table[self.register]
        return self._instruction_pointer + 1

    def _read(self) -> int:
        if not self._in:
            self._exception = (
                f"Nothing left to read at instruction {self._instruction_pointer}"
            )
            return -1

        char = self._in[0]
        if char not in self._table:
            self._exception = f"Cannot encode character '{char}' at instruction {self._instruction_pointer}"
            return -1

        self._in = self._in[1:]
        self.register = self._table.find(char)
        return self._instruction_pointer + 1

    def _find_next_back_jump(self) -> int:
        index = self._code.find("]", self._instruction_pointer + 1)
        if index < 0:
            self._exception = (
                f"No back jump found after the instruction {self._instruction_pointer}"
            )
        return index
