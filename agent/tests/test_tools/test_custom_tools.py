"""Tests for custom tools."""

import pytest

from src.tools.custom_tools import letter_counter


class TestLetterCounter:
    """Test cases for the letter_counter tool."""

    def test_letter_counter_basic(self):
        """Test basic letter counting functionality."""
        assert letter_counter("hello", "l") == 2
        assert letter_counter("world", "o") == 1
        assert letter_counter("python", "p") == 1

    def test_letter_counter_case_insensitive(self):
        """Test that letter counting is case insensitive."""
        assert letter_counter("Hello", "h") == 1
        assert letter_counter("Hello", "H") == 1
        assert letter_counter("WORLD", "w") == 1
        assert letter_counter("WORLD", "W") == 1

    def test_letter_counter_no_matches(self):
        """Test letter counting when letter is not found."""
        assert letter_counter("hello", "x") == 0
        assert letter_counter("world", "z") == 0

    def test_letter_counter_invalid_letter_length(self):
        """Test that multi-character letters raise ValueError."""
        with pytest.raises(ValueError, match="must be a single character"):
            letter_counter("hello", "ll")

        with pytest.raises(ValueError, match="must be a single character"):
            letter_counter("hello", "")

    def test_letter_counter_special_characters(self):
        """Test letter counting with special characters."""
        assert letter_counter("hello!", "!") == 1
        assert letter_counter("test@example.com", "@") == 1
        assert letter_counter("a-b-c", "-") == 2
