from __future__ import annotations

import json
import sys
from os import environ
from pathlib import Path
from typing import Any, Optional

from defargs.field import NODEFAULT, Config, Field


def json_loader(file: Path) -> dict[str, Any]:
    with open(file, "r") as f:
        return json.load(f)


def yaml_loader(file: Path) -> dict[str, Any]:
    import yaml

    with open(file, "r") as f:
        return yaml.load(f)


def toml_loader(file: Path) -> dict[str, Any]:
    if sys.version_info >= (3, 11):
        from tomllib import load as toml_load
    else:
        from tomli import load as toml_load
    with open(file, "rb") as f:
        return toml_load(f)


CONFIG_LOADER = {
    "json": json_loader,
    "yaml": yaml_loader,
    "yml": yaml_loader,
    "toml": toml_loader,
}


class CommandParser:
    def __init__(self, fields: list[Field], config: Config) -> None:
        self.config = config
        self.arguments: dict[str, Any] = {}
        self.known_keys: set[str] = set()
        self.unknown_fields: list[str] = []
        self.updated_by_env: list[str] = []
        self.updated_by_conf: list[str] = []
        self.short_key_map: dict[str, str] = {}
        self.key_type_map: dict[str, type] = {}

        for field in fields:
            self.known_keys.add(field.name)
            self.key_type_map[field.name] = field.field_type
            if field.short:
                self.short_key_map[field.short] = field.name
                self.key_type_map[field.short] = field.field_type
            if field.default is not NODEFAULT:
                self.arguments[field.name] = field.default
            elif field.default_factory is not NODEFAULT:
                self.arguments[field.name] = field.default_factory()

    def normalize(self, key: str, is_short_key: bool = False) -> str:
        if is_short_key:
            return self.short_key_map[key]
        return key.replace("-", "_")

    def load_env(self):
        if not self.config.from_env:
            return
        for key in self.arguments:
            env_key = (
                key
                if not self.config.env_prefix
                else f"{self.config.env_prefix}_{key.upper()}"
            )
            if env_key in environ:
                self.arguments[key] = environ[env_key]
                self.updated_by_env.append(key)

    def load_config_file(self):
        if not self.config.config_file:
            return
        file = Path(self.config.config_file)
        if not file.is_file():
            return
        config = CONFIG_LOADER[file.suffix[1:]](file)
        for key in self.arguments:
            if key in config:
                self.arguments[key] = config[key]
                self.updated_by_conf.append(key)

    def parse(self, args: Optional[list[str]] = None):  # noqa: PLR0912
        self.load_env()
        self.load_config_file()
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
