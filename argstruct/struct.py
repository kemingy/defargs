from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from typing import Optional, get_type_hints

from argstruct.field import NODEFAULT, Field
from argstruct.parser import CommandParser


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


@dataclass
class Config:
    name: Optional[str] = None
    config_file: Optional[str] = None
    from_env: bool = False
    env_prefix: Optional[str] = None
    callback: Optional[Callable[[ArgStruct], None]] = None


class ArgStruct:
    _config: Config

    def __init_subclass__(
        cls,
        name: Optional[str] = None,
        config_file: Optional[str] = None,
        from_env: bool = False,
        env_prefix: Optional[str] = None,
        callback: Optional[Callable[[ArgStruct], None]] = None,
    ):
        cls._config = Config(
            name=name,
            config_file=config_file,
            from_env=from_env,
            env_prefix=env_prefix,
            callback=callback,
        )

    @classmethod
    def __struct_fields__(cls) -> dict[str, Field]:
        """Get the fields of the struct.

        Includes:
        - fields with annotations
        - fields with default values that are instances of :py:class:`argstruct.field.Field`
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
            if name not in fields:
                # without default value
                fields[name] = Field(name=name, field_type=typ)
            else:
                fields[name].field_type = typ

        return fields

    @classmethod
    def parse_args(cls, execute: bool = True):
        """Parse command line arguments.

        Priority: command line > environment > config file > defaults

        If `execute` is set, it will trigger the callback with this structure instance.
        """
        fields = cls.__struct_fields__()
        parser = CommandParser(fields.values())
        args = parser.parse()

        if "help" in args or len(args) == 0:
            show_help_message(cls._config.name or cls.__name__, cls.__doc__, fields)
            return

        instance = cls()
        for key, value in args.items():
            if key not in fields:
                continue
            setattr(instance, key, value)

        if execute and cls._config.callback:
            cls._config.callback(instance)

        return instance


if __name__ == "__main__":

    class MyArgStruct(ArgStruct, name="cli", from_env=True, env_prefix="KEY"):
        pass

    MyArgStruct.parse_args()
