"""
Progress Display Module for BitTorrent DHT Crawler

This module provides functions for displaying real-time progress
information during DHT network crawling operations.

Functions:
    format_elapsed_time: Format seconds as HH:MM:SS
    calculate_rate: Calculate items per minute
    format_progress_line: Format a complete progress line
    clear_progress_line: Get ANSI code to clear current line
"""


def format_elapsed_time(seconds: float) -> str:
    """
    Format elapsed time in seconds as HH:MM:SS string.

    Args:
        seconds: Time in seconds (non-negative)

    Returns:
        str: Formatted time string (e.g., "01:23:45")

    Raises:
        ValueError: If seconds is negative
        TypeError: If seconds is not a number
    """
    # Type validation
    if not isinstance(seconds, (int, float)):
        raise TypeError(f"seconds must be a number, got {type(seconds).__name__}")

    # Value validation
    if seconds < 0:
        raise ValueError("seconds cannot be negative")

    # Convert to integer seconds
    total_seconds = int(seconds)

    # Calculate hours, minutes, seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_rate(count: int, elapsed: float) -> float:
    """
    Calculate rate as items per minute.

    Args:
        count: Number of items (non-negative)
        elapsed: Elapsed time in seconds (non-negative)

    Returns:
        float: Rate in items per minute (0.0 if elapsed is 0)

    Raises:
        ValueError: If count or elapsed is negative
        TypeError: If parameters are not numeric
    """
    # Type validation
    if not isinstance(count, int):
        raise TypeError(f"count must be an integer, got {type(count).__name__}")

    if not isinstance(elapsed, (int, float)):
        raise TypeError(f"elapsed must be a number, got {type(elapsed).__name__}")

    # Value validation
    if count < 0:
        raise ValueError("count cannot be negative")

    if elapsed < 0:
        raise ValueError("elapsed cannot be negative")

    # Handle zero elapsed time
    if elapsed == 0.0:
        return 0.0

    # Calculate rate: items per minute
    rate = (count / elapsed) * 60.0

    return rate


def format_progress_line(
    elapsed: float,
    count: int,
    rate: float,
    total_requests: int,
    table_size: int
) -> str:
    """
    Format a progress line with all statistics.

    Args:
        elapsed: Elapsed time in seconds (non-negative)
        count: Number of unique info_hashes (non-negative)
        rate: Discovery rate in items/minute (non-negative)
        total_requests: Total requests received (non-negative)
        table_size: Routing table size (non-negative)

    Returns:
        str: Formatted progress line

    Raises:
        ValueError: If any parameter is negative
    """
    # Validate all parameters are non-negative
    if elapsed < 0:
        raise ValueError("elapsed cannot be negative")
    if count < 0:
        raise ValueError("count cannot be negative")
    if rate < 0:
        raise ValueError("rate cannot be negative")
    if total_requests < 0:
        raise ValueError("total_requests cannot be negative")
    if table_size < 0:
        raise ValueError("table_size cannot be negative")

    # Format elapsed time
    time_str = format_elapsed_time(elapsed)

    # Format the progress line
    progress = (
        f"[{time_str}] "
        f"Unique: {count:4d} | "
        f"Rate: {rate:5.1f}/min | "
        f"Requests: {total_requests:5d} | "
        f"Nodes: {table_size:3d}"
    )

    return progress


def clear_progress_line() -> str:
    """
    Get ANSI escape code to clear the current line.

    Returns:
        str: ANSI escape sequence to clear and reset cursor
    """
    # ANSI escape codes:
    # \r = carriage return (move to start of line)
    # \033[K = clear from cursor to end of line
    return "\r\033[K"
