"""Parse and format work durations as H:MM (hours:minutes)."""

from typing import Union


def parse_time_input(text: str, max_hours: int = 20) -> float:
    """
    Parse user input like '6', '2:30', '0:30' into decimal hours.
    Rejects dot-separated values like '6.5' or '2.30'.
    """
    text = text.strip()
    if not text:
        raise ValueError("empty")

    if "." in text:
        raise ValueError("dot not allowed")

    if ":" in text:
        parts = text.split(":", 1)
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            raise ValueError("invalid format")
        hours = int(parts[0])
        minutes = int(parts[1])
        if minutes < 0 or minutes >= 60:
            raise ValueError("minutes out of range")
        total_hours = hours + minutes / 60.0
    elif text.isdigit():
        total_hours = float(int(text))
    else:
        raise ValueError("invalid format")

    if total_hours < 0 or total_hours > max_hours:
        raise ValueError("out of range")

    return total_hours


def format_duration(hours: Union[float, int, None]) -> str:
    """Format decimal hours as H:MM."""
    if hours is None:
        hours = 0.0
    total_minutes = int(round(float(hours) * 60))
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h}:{m:02d}"


def _self_check() -> None:
    assert parse_time_input("1:30") == 1.5
    assert parse_time_input("1:20") == 1 + 20 / 60
    total = parse_time_input("1:30") + parse_time_input("1:20")
    assert format_duration(total) == "2:50"
    assert parse_time_input("2:30") == 2.5
    assert format_duration(2.5) == "2:30"
    assert format_duration(0.5) == "0:30"
    try:
        parse_time_input("2.30")
        raise AssertionError("expected ValueError for dot format")
    except ValueError as e:
        assert "dot" in str(e)


if __name__ == "__main__":
    _self_check()
    print("ok")
