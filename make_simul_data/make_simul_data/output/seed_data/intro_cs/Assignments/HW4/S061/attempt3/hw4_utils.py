"""HW4 Utility Functions: Recursive and iterative implementations.
Provides helper functions for prime checking, factorial, list
operations, string manipulation, and GCD computation.
"""

def is_prime(n: int) -> bool:
    """Check if n is prime using trial division.

    Args:
        n: The integer to check.

    Returns:
        True if n is a prime number.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def factorial(n: int) -> int:
    """Compute n! recursively.

    Args:
        n: Non-negative integer.

    Returns:
        n factorial.
    """
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def find_max(numbers: list[int]) -> int:
    """Find the largest element in a list.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        Maximum value in the list.
    """
    max_value: int = numbers[0]
    for num in numbers:
        if num > max_value:
            max_value = num
    return max_value


def reverse_string(text: str) -> str:
    """Reverse a string using slicing.

    Args:
        text: String to reverse.

    Returns:
        The reversed string.
    """
    return text[::-1]

def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome.

    Args:
        text: String to check.

    Returns:
        True if text is a palindrome.
    """
    return text == text[::-1]

def power(base: int, exponent: int) -> int:
    """Compute base^exponent recursively.

    Args:
        base: Base number.
        exponent: Non-negative exponent.

    Returns:
        base raised to the exponent.
    """
    if exponent == 0:
        return 1
    return base * power(base, exponent - 1)

def gcd(a: int, b: int) -> int:
    """Compute GCD using recursive Euclidean algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.

    Returns:
        Greatest common divisor.
    """
    if b == 0:
        return a
    return gcd(b, a % b)