from __future__ import annotations

from defargs import DefArgs, field


class TestDefArgs(DefArgs, name="test"):
    file: str = field(help="File to read from")
    timeout: int = field(default=10, help="Timeout in seconds")
    verbose: bool
    cpus: list[int] = field(default_factory=list, short="c", help="List of CPUs to use")

    # exclude since it's not annotated and the default value is not a `Field`
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
            "--unknown",
            "unknown",
        ],
    )
    args = TestDefArgs.parse_args()
    assert args.file == "test.txt"
    assert args.timeout == "1"
    assert args.verbose is True
    assert args.cpus == ["1", "2"]

    assert args.unknown is None
