"""HW2 Solution: Conditionals and Boolean Logic.
Implements grade classification and leap year checking
using structured conditional expressions.
"""

def get_letter_grade(score: int) -> str:
    """Convert a numeric score to a letter grade.

    Args:
        score: Integer score from 0 to 100.

    Returns:
        Letter grade as a string.
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


def check_leap_year(year: int) -> bool:
    """Check if a year is a leap year using the Gregorian calendar rules.

    Args:
        year: The year to evaluate.

    Returns:
        True if leap year, False otherwise.
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def main() -> None:
    """Run grade and leap year programs."""
    score: int = int(input())
    print(get_letter_grade(score))

    year: int = int(input())
    print(check_leap_year(year))


if __name__ == "__main__":
    main()