from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from defargs.field import Config, Field


class CommandParser:
    def __init__(self, fields: list[Field], config: Config) -> None:
        self.arguments: dict[str, Any] = {}
        self.known_keys: set[str] = set()
        self.unknown_fields: list[str] = []
        self.short_key_map: dict[str, str] = {}
        self.key_type_map: dict[str, type] = {}

        for field in fields:
            self.known_keys.add(field.name)
            self.key_type_map[field.name] = field.field_type
            if field.short:
                self.short_key_map[field.short] = field.name
                self.key_type_map[field.short] = field.field_type

    def normalize(self, key: str, is_short_key: bool = False) -> str:
        if is_short_key:
            return self.short_key_map[key]
        return key.replace("-", "_")

    def parse(self, args: Optional[list[str]] = None):  # noqa: PLR0912
        if args is None:
            args = sys.argv[1:]

        length = len(args)
        index = 0

        while index < length:
            arg = args[index]
            key: str = ""
            value: str = ""
            is_short_key = False
            if arg.startswith("--"):
                key = arg[2:]
            elif arg.startswith("-"):
                # TODO: support multiple short keys in one argument
                key = arg[1:]
                is_short_key = True
            else:
                raise ValueError(
                    f"invalid argument when parsing `{args}` at word {index}: lack of dash"
                )

            if "=" in key:
                key, value = key.split("=", 1)
            elif key not in self.key_type_map:
                # unknown key
                self.unknown_fields.append(key)
                # clean the associated values
                if index + 1 < length and not args[index + 1].startswith("-"):
                    index += 1
                    self.unknown_fields.append(args[index])
            elif self.key_type_map[key] is bool:
                value = True
            elif index + 1 < length:
                index += 1
                value = args[index]
            else:
                raise ValueError(
                    f"invalid argument when parsing `{args}` at word {index}: lack of value"
                )

            key = self.normalize(key, is_short_key=is_short_key)
            if key not in self.arguments:
                self.arguments[key] = value
            elif isinstance(self.arguments[key], list):
                self.arguments[key].append(value)
            elif getattr(self.key_type_map[key], "__origin__", None) is list:
                self.arguments[key] = [self.arguments[key], value]
            else:
                # override
                self.arguments[key] = value

            index += 1

        return self.arguments
