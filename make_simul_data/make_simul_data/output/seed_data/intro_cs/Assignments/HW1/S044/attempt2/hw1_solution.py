"""HW1 Solution: Variables, I/O, and Arithmetic Operations.

This module implements basic arithmetic operations including
addition, temperature conversion, area calculation, and
integer division with modulus.

Author: Student
Course: CS1 - Introduction to Computer Science
"""
import math


def add_two_numbers(a: int, b: int) -> int:
    """Return the sum of two integers.

    Args:
        a: First integer operand.
        b: Second integer operand.

    Returns:
        The sum a + b.
    """
    return a + b

def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit.
    Uses the standard formula: F = C * 9/5 + 32

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit.
    """
    return celsius * 9 / 5 + 32

def circle_area(radius: float) -> float:
    """Calculate the area of a circle given its radius.
    Uses math.pi for precision and rounds to 2 decimal places.
    Args:
        radius: The radius of the circle.

    Returns:
        The area of the circle, rounded to 2 decimal places.
    """
    return round(math.pi * radius ** 2, 2)

def integer_division(a: int, b: int) -> tuple[int, int]:
    """Perform integer division and return quotient and remainder.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        A tuple of (quotient, remainder).
    """
    return a // b, a % b


def main() -> None:
    """Main function to run all arithmetic problems."""
    # Problem 1: Add two integers
    x = int(input())
    y = int(input())
    print(add_two_numbers(x, y))
    # Problem 2-3: Celsius to Fahrenheit conversion
    celsius = float(input())
    print(celsius_to_fahrenheit(celsius))

    # Problem 4: Circle area calculation
    radius = float(input())
    print(circle_area(radius))

    # Problem 5: Integer division and modulus
    dividend = int(input())
    divisor = int(input())
    quotient, remainder = integer_division(dividend, divisor)
    print(quotient)
    print(remainder)

if __name__ == "__main__":
    main()