"""HW2 Solution: Conditionals and Boolean Logic.
Uses clear function decomposition for grade classification
and leap year determination.
"""


def assign_grade(score: int) -> str:
    """Assign a letter grade based on the score.

    Grading thresholds: A>=90, B>=80, C>=70, D>=60, F<60.
    Args:
        score: The numeric score to classify.

    Returns:
        The corresponding letter grade.
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def is_leap_year(year: int) -> bool:
    """Determine whether the given year is a leap year.

    Leap year rules:
        - Divisible by 4 AND not by 100, OR divisible by 400.
    Args:
        year: Calendar year as a positive integer.
    Returns:
        True if the year is a leap year.
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0
def main() -> None:
    """Entry point: process grade and leap year inputs."""
    score: int = int(input())
    print(assign_grade(score))
    year: int = int(input())
    print(is_leap_year(year))


if __name__ == "__main__":
    main()
