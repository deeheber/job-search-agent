"""Custom tools for the agent."""

from strands import tool


@tool
def letter_counter(word: str, letter: str) -> int:
    """Count how many times a letter appears in a word.

    Args:
        word: The word to search in
        letter: The letter to count (must be a single character)

    Returns:
        The number of times the letter appears in the word (case-insensitive)

    Raises:
        ValueError: If letter is not a single character
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())
