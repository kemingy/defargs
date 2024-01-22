from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import partial
from typing import Optional, get_type_hints

from defargs.field import NODEFAULT, Config, Field
from defargs.parser import CommandParser


def show_help_message(name: str, description: Optional[str], fields: dict[str, Field]):
    println = partial(print, end="\n\n")
    print_span = partial(print, end="")
    span_indent = "  "

    println(f"{name} [Command Line Interface]")
    if description:
        println(description)
    println("Usage:")
    for field in fields.values():
        if field.short:
            print_span(f"{span_indent}-{field.short}, --{field.name}")
        else:
            print_span(f"{span_indent}--{field.name}")
        required = field.default is NODEFAULT and field.default_factory is NODEFAULT
        print_span(f"{span_indent}[required={required}]")
        if field.help:
            print_span(f"{span_indent}{field.help}")
        print()


class DefArgs:
    __args_config__: Config

    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        config_file: Optional[str] = None,
        from_env: bool = False,
        env_prefix: Optional[str] = None,
    ):
        cls.__args_config__ = Config(
            name=name,
            config_file=config_file,
            from_env=from_env,
            env_prefix=env_prefix,
        )

    @classmethod
    def __struct_fields__(cls) -> dict[str, Field]:
        """Get the fields of the struct.

        Includes:
        - fields with annotations
        - fields with default values that are instances of :py:class:`defargs.field.Field`
        """
        fields = {
            "help": Field(
                name="help",
                field_type=bool,
                default=False,
                default_factory=None,
                short="h",
                help="help message",
            )
        }

        for name, field in inspect.getmembers(cls, lambda x: isinstance(x, Field)):
            if field.name is None:
                field.name = name
            fields[name] = field

        for name, typ in get_type_hints(cls).items():
            if name.startswith("__"):
                continue
            if name not in fields:
                # without default value
                fields[name] = Field(name=name, field_type=typ)
            else:
                fields[name].field_type = typ

        return fields

    @classmethod
    def parse_args(cls, callback: Optional[Callable[[DefArgs], None]] = None):
        """Parse command line arguments.

        Priority: command line > environment > config file > defaults

        Args:
            callback: callback function to be called after parsing arguments,
                with the parsed arguments as the only argument
        """
        fields = cls.__struct_fields__()
        parser = CommandParser(fields.values(), cls.__args_config__)
        known_args = parser.parse()

        # `help` is a reserved keyword
        if known_args["help"] or len(known_args) == 1:
            show_help_message(
                cls.__args_config__.name or cls.__name__, cls.__doc__, fields
            )
            return

        instance = cls()
        for key, value in known_args.items():
            if key not in fields:
                continue
            setattr(instance, key, value)

        if callback:
            callback(instance)

        return instance


if __name__ == "__main__":

    class MyArg(DefArgs, name="cli", from_env=True, env_prefix="KEY"):
        name: str
        enabled: bool

    MyArg.parse_args()
