#!/usr/bin/env python3
"""
Unit tests for progress_display module.

Tests the progress display functionality used in CRAWLER mode
with INFINITE duration.
"""

import unittest
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from progress_display import (
    format_elapsed_time,
    calculate_rate,
    format_progress_line,
    clear_progress_line
)


class TestFormatElapsedTime(unittest.TestCase):
    """Test the format_elapsed_time function."""

    def test_format_zero_seconds(self):
        """Test formatting 0 seconds."""
        result = format_elapsed_time(0.0)
        self.assertEqual(result, "00:00:00")

    def test_format_less_than_minute(self):
        """Test formatting time less than 1 minute."""
        result = format_elapsed_time(45.5)
        self.assertEqual(result, "00:00:45")

    def test_format_exactly_one_minute(self):
        """Test formatting exactly 1 minute."""
        result = format_elapsed_time(60.0)
        self.assertEqual(result, "00:01:00")

    def test_format_hours_minutes_seconds(self):
        """Test formatting time with hours, minutes, and seconds."""
        # 1 hour, 23 minutes, 45 seconds
        result = format_elapsed_time(5025.0)
        self.assertEqual(result, "01:23:45")

    def test_format_more_than_24_hours(self):
        """Test formatting time more than 24 hours."""
        # 25 hours, 30 minutes, 15 seconds
        result = format_elapsed_time(91815.0)
        self.assertEqual(result, "25:30:15")

    def test_format_negative_time_raises_error(self):
        """Test that negative time raises ValueError."""
        with self.assertRaises(ValueError) as context:
            format_elapsed_time(-10.0)
        self.assertIn("negative", str(context.exception).lower())

    def test_format_invalid_type_raises_error(self):
        """Test that invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            format_elapsed_time("not a number")


class TestCalculateRate(unittest.TestCase):
    """Test the calculate_rate function."""

    def test_calculate_rate_normal(self):
        """Test calculating rate with normal values."""
        # 60 items in 60 seconds = 60 items/minute
        result = calculate_rate(60, 60.0)
        self.assertAlmostEqual(result, 60.0, places=2)

    def test_calculate_rate_30_seconds(self):
        """Test calculating rate for 30 seconds."""
        # 30 items in 30 seconds = 60 items/minute
        result = calculate_rate(30, 30.0)
        self.assertAlmostEqual(result, 60.0, places=2)

    def test_calculate_rate_zero_count(self):
        """Test rate when count is zero."""
        result = calculate_rate(0, 60.0)
        self.assertEqual(result, 0.0)

    def test_calculate_rate_zero_elapsed(self):
        """Test rate when elapsed time is zero (should return 0 to avoid division by zero)."""
        result = calculate_rate(10, 0.0)
        self.assertEqual(result, 0.0)

    def test_calculate_rate_fractional(self):
        """Test rate calculation with fractional values."""
        # 5 items in 10 seconds = 30 items/minute
        result = calculate_rate(5, 10.0)
        self.assertAlmostEqual(result, 30.0, places=2)

    def test_calculate_rate_negative_count_raises_error(self):
        """Test that negative count raises ValueError."""
        with self.assertRaises(ValueError) as context:
            calculate_rate(-5, 60.0)
        self.assertIn("negative", str(context.exception).lower())

    def test_calculate_rate_negative_elapsed_raises_error(self):
        """Test that negative elapsed time raises ValueError."""
        with self.assertRaises(ValueError) as context:
            calculate_rate(10, -60.0)
        self.assertIn("negative", str(context.exception).lower())

    def test_calculate_rate_invalid_type_raises_error(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            calculate_rate("10", 60.0)
        with self.assertRaises(TypeError):
            calculate_rate(10, "60")


class TestFormatProgressLine(unittest.TestCase):
    """Test the format_progress_line function."""

    def test_format_progress_line_normal(self):
        """Test formatting progress line with normal values."""
        result = format_progress_line(
            elapsed=125.0,
            count=42,
            rate=20.5,
            total_requests=150,
            table_size=87
        )

        # Verify all components are present
        self.assertIn("00:02:05", result)  # elapsed time
        self.assertIn("42", result)         # count
        self.assertIn("20.5", result)       # rate
        self.assertIn("150", result)        # total_requests
        self.assertIn("87", result)         # table_size

    def test_format_progress_line_zero_values(self):
        """Test formatting progress line with zero values."""
        result = format_progress_line(
            elapsed=0.0,
            count=0,
            rate=0.0,
            total_requests=0,
            table_size=0
        )

        # Should handle zeros gracefully
        self.assertIn("00:00:00", result)
        self.assertIn("0", result)

    def test_format_progress_line_large_values(self):
        """Test formatting progress line with large values."""
        result = format_progress_line(
            elapsed=36000.0,  # 10 hours
            count=5000,
            rate=123.45,
            total_requests=10000,
            table_size=500
        )

        self.assertIn("10:00:00", result)
        self.assertIn("5000", result)

    def test_format_progress_line_negative_values_raise_error(self):
        """Test that negative values raise ValueError."""
        with self.assertRaises(ValueError):
            format_progress_line(-10.0, 10, 5.0, 100, 50)

        with self.assertRaises(ValueError):
            format_progress_line(10.0, -10, 5.0, 100, 50)

        with self.assertRaises(ValueError):
            format_progress_line(10.0, 10, -5.0, 100, 50)

        with self.assertRaises(ValueError):
            format_progress_line(10.0, 10, 5.0, -100, 50)

        with self.assertRaises(ValueError):
            format_progress_line(10.0, 10, 5.0, 100, -50)


class TestClearProgressLine(unittest.TestCase):
    """Test the clear_progress_line function."""

    def test_clear_progress_line_returns_string(self):
        """Test that clear_progress_line returns a string."""
        result = clear_progress_line()
        self.assertIsInstance(result, str)

    def test_clear_progress_line_contains_ansi_codes(self):
        """Test that clear_progress_line contains ANSI escape codes."""
        result = clear_progress_line()
        # Should contain carriage return or ANSI codes
        self.assertTrue('\r' in result or '\033[' in result or '\x1b[' in result)


def run_tests():
    """Run all tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
