"""HW2 Solution: Conditionals and Boolean Logic.

This module implements grade classification based on numeric scores
and leap year determination using conditional statements.
Author: Student
Course: CS1 - Introduction to Computer Science
"""
def classify_grade(score: int) -> str:
    """Classify a numeric score into a letter grade.
    Grading scale:
        A: score >= 90
        B: 80 <= score < 90
        C: 70 <= score < 80
        D: 60 <= score < 70
        F: score < 60

    Args:
        score: Numeric score (0-100).

    Returns:
        A single letter grade string ("A", "B", "C", "D", or "F").
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
def is_leap_year(year: int) -> bool:
    """Determine whether a given year is a leap year.

    A year is a leap year if:
        1. It is divisible by 4, AND
        2. It is NOT divisible by 100, UNLESS
        3. It is also divisible by 400.

    Args:
        year: The year to check (positive integer).
    Returns:
        True if the year is a leap year, False otherwise.
    """
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False


def main() -> None:
    """Main function: read inputs and print results."""
    # Grade classification
    score: int = int(input())
    print(classify_grade(score))
    # Leap year check
    year: int = int(input())
    print(is_leap_year(year))


if __name__ == "__main__":
    main()
