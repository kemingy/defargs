from __future__ import annotations

from argstruct import ArgStruct, field


class TestArgStruct(ArgStruct, name="test"):
    file: str = field(help="File to read from")
    timeout: int = field(default=10, help="Timeout in seconds")
    verbose: bool
    cpus: list[int] = field(default_factory=list, short="c", help="List of CPUs to use")

    # exclude
    unknown = None


def test_basic(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "test.py",
            "--file",
            "test.txt",
            "--timeout",
            "1",
            "--verbose",
            "--cpus",
            "1",
            "-c",
            "2",
        ],
    )
    args = TestArgStruct.parse_args()
    assert args.file == "test.txt"
    assert args.timeout == "1"
    assert args.verbose is True
    assert args.cpus == ["1", "2"]
