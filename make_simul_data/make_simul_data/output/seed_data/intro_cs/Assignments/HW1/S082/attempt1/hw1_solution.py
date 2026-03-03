"""HW1 Solution: Variables, I/O, and Arithmetic.

Demonstrates basic Python operations: integer arithmetic,
floating-point conversion, mathematical constants, and
the modulo operator.
"""

import math

def main() -> None:
    """Execute all arithmetic problems sequentially."""
    # Problem 1: Read two integers and print their sum.
    num1: int = int(input())
    num2: int = int(input())
    total: int = num1 + num2
    print(total)
    # Problem 2-3: Convert Celsius to Fahrenheit.
    # Formula: F = C * (9/5) + 32
    temp_celsius: float = float(input())
    temp_fahrenheit: float = temp_celsius * 9 / 5 + 32
    print(temp_fahrenheit)

    # Problem 4: Compute circle area using A = pi * r^2.
    radius: float = float(input())
    area: float = round(math.pi * radius ** 2, 2)
    print(area)
    # Problem 5: Integer division and modulus.
    dividend: int = int(input())
    divisor: int = int(input())
    print(dividend // divisor)
    print(dividend % divisor)

if __name__ == "__main__":
    main()



# ============================================================
# Student Notes
# ============================================================
# Alternative approach: could use list comprehension for a more Pythonic style.
