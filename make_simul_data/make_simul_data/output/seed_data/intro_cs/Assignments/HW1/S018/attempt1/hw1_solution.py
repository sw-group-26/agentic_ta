"""HW1 Solution: Variables, I/O, and Arithmetic Operations.

This module uses a structured approach with named functions
for each arithmetic problem. Each function reads its own
input and prints the result.
"""
import math

def problem_addition() -> None:
    """Read two integers and print their sum."""
    a: int = int(input())
    b: int = int(input())
    result: int = a + b
    print(result)


def problem_celsius_to_fahrenheit() -> None:
    """Read a Celsius temperature and print it in Fahrenheit.

    Formula: F = C * 9/5 + 32
    """
    celsius: float = float(input())
    fahrenheit: float = celsius * 9.0 / 5.0 + 32.0
    print(fahrenheit)

def problem_circle_area() -> None:
    """Read a radius and print the area of the circle.
    Uses math.pi for maximum precision, rounded to 2 decimal places.
    """
    radius: float = float(input())
    area: float = round(math.pi * radius ** 2, 2)
    print(area)

def problem_integer_division() -> None:
    """Read two integers and print quotient and remainder."""
    a: int = int(input())
    b: int = int(input())
    print(a // b)
    print(a % b)

def main() -> None:
    """Run all problems in sequence."""
    problem_addition()
    problem_celsius_to_fahrenheit()
    problem_circle_area()
    problem_integer_division()

if __name__ == "__main__":
    main()
