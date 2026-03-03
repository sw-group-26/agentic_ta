"""HW4 Utilities: Mathematical and string helper functions.
Provides reusable functions for prime checking, factorial computation,
list operations, string manipulation, and number theory.
"""
import math


def is_prime(n: int) -> bool:
    """Test primality using trial division up to sqrt(n).

    Args:
        n: Integer to test.
    Returns:
        True if n is prime.
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i: int = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def factorial(n: int) -> int:
    """Compute factorial iteratively.

    Args:
        n: Non-negative integer.

    Returns:
        n! (n factorial).
    """
    return math.prod(range(1, n + 1)) if n > 0 else 1


def find_max(numbers: list[int]) -> int:
    """Return the maximum element from a list.
    Args:
        numbers: Non-empty list of integers.

    Returns:
        The maximum value.
    """
    maximum: int = numbers[0]
    for num in numbers[1:]:
        if num > maximum:
            maximum = num
    return maximum


def reverse_string(s: str) -> str:
    """Reverse a string using slicing.

    Args:
        s: Input string.

    Returns:
        Reversed string.
    """
    return s[::-1]


def is_palindrome(s: str) -> bool:
    """Check whether a string reads the same forwards and backwards.

    Args:
        s: Input string.

    Returns:
        True if s is a palindrome.
    """
    return s == s[::-1]

def power(base: int, exp: int) -> int:
    """Compute base^exp iteratively.

    Args:
        base: Base integer.
        exp: Non-negative exponent.

    Returns:
        base raised to the power of exp.
    """
    result: int = 1
    for _ in range(exp):
        result *= base
    return result


def gcd(a: int, b: int) -> int:
    """Greatest common divisor via Euclid's algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.
    Returns:
        GCD(a, b).
    """
    while b:
        a, b = b, a % b
    return a
