from dataclasses import dataclass
from enum import Enum
from typing import Optional, overload


class UNSET_TYPE(Enum):
    NODEFAULT = "NO_DEFAULT"


NODEFAULT = UNSET_TYPE.NODEFAULT


@dataclass
class Field:
    default: object = NODEFAULT
    default_factory: object = NODEFAULT
    name: Optional[str] = None
    short: Optional[str] = None
    help: Optional[str] = None
    field_type: Optional[type] = None


@overload
def field(*, default=NODEFAULT, name=None, short=None, help=None):
    """Create a field with default value.

    Args:
        default (object): default value
        name (Optional[str]): name alias
        short (Optional[str]): short name
        help (Optional[str]): help message
    """
    pass


@overload
def field(*, default_factory=NODEFAULT, name=None, short=None, help=None):
    """Create a field with default factory.

    Args:
        default_factory (object): default factory
        name (Optional[str]): name alias
        short (Optional[str]): short name
        help (Optional[str]): help message
    """
    pass


def field(
    *, default=NODEFAULT, default_factory=NODEFAULT, name=None, short=None, help=None
):
    if default is not NODEFAULT and default_factory is not NODEFAULT:
        raise ValueError("cannot specify both default and default_factory")
    return Field(
        default=default,
        default_factory=default_factory,
        name=name,
        short=short,
        help=help,
    )


@dataclass
class Config:
    name: Optional[str] = None
    config_file: Optional[str] = None
    from_env: bool = False
    env_prefix: Optional[str] = None

