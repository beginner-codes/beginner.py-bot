import re
from collections import defaultdict
from typing import AnyStr, Callable, Coroutine, List, Tuple, Union


class ExtensionMeta(type):
    def __new__(mcs, name, bases, attrs, flag: AnyStr = ""):
        cls = type.__new__(mcs, name, bases, attrs)
        cls.__bot_flag__ = flag
        cls.__bot_commands__ = defaultdict(list)
        return cls

    def __init__(*args, **_):
        type.__init__(*args)

    def __init_subclass__(cls, **kwargs):
        pass


class Extension(metaclass=ExtensionMeta):
    # Properties
    @property
    def flag(self) -> AnyStr:
        return self.__bot_flag__

    # Decorators
    @classmethod
    def command(
        cls,
        name: Union[AnyStr, None] = None,
        options: int = 0,
        beginning: bool = True,
        consume_all: bool = False,
    ) -> Callable:
        def _decorator(callback: Coroutine) -> "Command":
            _name = name if name else callback.__name__
            command = Command(_name, callback, options, beginning, consume_all)
            cls.__bot_commands__[_name].append(command)
            return command

        return _decorator


class Command:
    def __init__(
        self,
        name: AnyStr,
        callback: Coroutine,
        options: int,
        beginning: bool = True,
        consume_all: bool = True,
    ):
        self._beginning = beginning
        self._callback = callback
        self._consume_all = consume_all
        self._name = name.lower()
        self._options = options
        self._subcommands = defaultdict(list)

    # Properties
    @property
    def beginning(self) -> bool:
        return self._beginning

    @property
    def consume_all(self) -> bool:
        return self._consume_all

    @property
    def name(self) -> AnyStr:
        return self._name

    @property
    def options(self) -> int:
        return self._options

    # Methods
    async def fail(self, ctx, reason: AnyStr):
        pass

    def get_options(self, raw_options: AnyStr) -> List[AnyStr,]:
        return re.findall(self._build_option_regex(), raw_options)

    def is_match(self, message: AnyStr, flag: AnyStr) -> bool:
        return bool(re.findall(self._build_command_regex(flag), message))

    async def run(self, ctx, message: AnyStr, flag: AnyStr) -> List[Tuple[AnyStr,]]:
        matches = re.findall(self._build_regex(flag), message)
        for match in matches:
            tokens = re.findall(r"([^\s]+)\s?(.+)?", match)
            if tokens:
                name, raw_options = tokens[0]
                subcommands = sorted(
                    self._subcommands.get(name, []), key=lambda command: command.options
                )
                for subcommand in subcommands:
                    if subcommand.are_options_a_match(raw_options):
                        if await subcommand.run(ctx, message):
                            break

            ## NEED TO
            ## We have the parsing for options working. Need to process that and
            ## find which subcommands match and then run the correct one and fail
            ## the appropriate command/subcommand if the options are incompatible
            ## with all

    def _build_command_regex(self, flag: AnyStr) -> AnyStr:
        beginning = "^" if self.beginning else ""
        flag = re.escape(flag)
        return f"{beginning}{flag}{self.name}"

    def _build_option_regex(self):
        option_count = self.options - 1 if self.consume_all else self.options
        options = [r"([^\s])"] * option_count if self.options else ["()"]
        if self.consume_all:
            options.append(r"(.+)")
        return r"\s".join(options)

    def _build_regex(self, flag: AnyStr) -> AnyStr:
        command = self._build_command_regex(flag)
        options = f"(?:\\s)?(.*?)(?:\\s)?(?={flag}[^\\s]+|$)"
        return f"{command}{options}"

    # Decorators
    def subcommand(
        self,
        name: Union[AnyStr, None] = None,
        options: int = 0,
        consume_all: bool = True,
    ) -> Callable:
        def _decorator(callback: Coroutine) -> "Command":
            _name = name if name else callback.__name__
            subcommand = Command(_name, callback, options, consume_all=consume_all)
            self._subcommands[_name].append(subcommand)
            return subcommand

        return _decorator


class MyExtension(Extension, flag="!"):
    @Extension.command(name="rule", options=1, consume_all=True, beginning=False)
    def single_all_consuming(self):
        pass

    @Extension.command(name="rule", options=0, consume_all=False, beginning=False)
    def no_options(self):
        pass

    @Extension.command(options=3, consume_all=False, beginning=True)
    def triple_beginning(self):
        pass


x = MyExtension()
x.single_all_consuming.run(
    "!rule !rule hi !rule -edit 1 !rule hello! how are you", x.flag
)
x.no_options.run("!rule !rule hi !rule -edit 1 !rule hello! how are you", x.flag)
x.triple_beginning.run("Hi there", x.flag)
