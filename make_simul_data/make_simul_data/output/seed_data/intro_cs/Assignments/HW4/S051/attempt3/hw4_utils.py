"""HW4 Utility Functions: Reusable helper functions.

This module provides mathematical and string utility functions
used by the main hw4_solution.py driver.
"""

def is_prime(n: int) -> bool:
    """Check if a number is prime.

    A prime number is greater than 1 and has no divisors other
    than 1 and itself. Uses trial division up to sqrt(n).

    Args:
        n: Integer to check.
    Returns:
        True if n is prime, False otherwise.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i: int = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def factorial(n: int) -> int:
    """Compute n! iteratively.
    Args:
        n: Non-negative integer.

    Returns:
        n factorial.
    """
    result: int = 1
    for i in range(2, n + 1):
        result *= i
    return result


def find_max(numbers: list[int]) -> int:
    """Find the maximum value in a list of integers.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        The largest integer in the list.
    """
    max_val: int = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val


def reverse_string(text: str) -> str:
    """Reverse a string.

    Args:
        text: The string to reverse.
    Returns:
        The reversed string.
    """
    return text[::-1]

def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome.

    Args:
        text: The string to check.
    Returns:
        True if text reads the same forwards and backwards.
    """
    return text == text[::-1]

def power(base: int, exponent: int) -> int:
    """Compute base raised to the exponent using a loop.
    Args:
        base: The base number.
        exponent: The exponent (non-negative integer).

    Returns:
        base ** exponent.
    """
    result: int = 1
    for _ in range(exponent):
        result *= base
    return result


def gcd(a: int, b: int) -> int:
    """Compute the greatest common divisor using Euclid's algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.
    Returns:
        The GCD of a and b.
    """
    while b != 0:
        a, b = b, a % b
    return a
