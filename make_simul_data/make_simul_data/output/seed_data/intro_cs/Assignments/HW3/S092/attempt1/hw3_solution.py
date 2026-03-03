"""HW3 Solution: Loops and Iteration.

This module demonstrates various loop-based algorithms including
summation, factorial, Fibonacci, and digit manipulation.
Author: Student
Course: CS1 - Introduction to Computer Science
"""

def sum_natural(n: int) -> int:
    """Calculate the sum of the first n natural numbers.

    Uses a for loop to accumulate 1 + 2 + ... + n.

    Args:
        n: Upper bound (positive integer).
    Returns:
        Sum of integers from 1 to n inclusive.
    """
    total: int = 0
    for i in range(1, n + 1):
        total += i
    return total

def factorial(n: int) -> int:
    """Calculate n! (n factorial) iteratively.

    Args:
        n: Non-negative integer.

    Returns:
        The factorial of n (n! = 1 * 2 * ... * n).
    """
    result: int = 1
    for i in range(1, n + 1):
        result *= i
    return result

def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (1-indexed).

    Sequence: 1, 1, 2, 3, 5, 8, 13, ...
    fibonacci(1) = 1, fibonacci(7) = 13.

    Args:
        n: Position in the Fibonacci sequence (1-indexed).

    Returns:
        The nth Fibonacci number.
    """
    if n <= 2:
        return 1
    a: int = 1
    b: int = 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b

def count_digits(number: int) -> int:
    """Count the number of digits in an integer.

    Args:
        number: A positive integer.

    Returns:
        The number of digits.
    """
    count: int = 0
    while number > 0:
        number //= 10
        count += 1
    return count


def reverse_number(number: int) -> int:
    """Reverse the digits of a positive integer.

    Example: 1234 -> 4321
    Args:
        number: A positive integer to reverse.

    Returns:
        The reversed number.
    """
    reversed_num: int = 0
    while number > 0:
        reversed_num = reversed_num * 10 + number % 10
        number //= 10
    return reversed_num


def sum_digits(number: int) -> int:
    """Calculate the sum of digits of a positive integer.

    Args:
        number: A positive integer.

    Returns:
        Sum of all digits.
    """
    total: int = 0
    while number > 0:
        total += number % 10
        number //= 10
    return total


def multiply(a: int, b: int) -> int:
    """Multiply two integers using repeated addition.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The product a * b.
    """
    result: int = 0
    for _ in range(b):
        result += a
    return result


def main() -> None:
    """Main function to execute all loop problems."""
    # Problem 1: Sum of first N natural numbers
    n1: int = int(input())
    print(sum_natural(n1))

    # Problem 2: Factorial
    n2: int = int(input())
    print(factorial(n2))

    # Problem 3: Fibonacci
    n3: int = int(input())
    print(fibonacci(n3))

    # Problem 4: Count digits
    n4: int = int(input())
    print(count_digits(n4))
    # Problem 5: Reverse number
    n5: int = int(input())
    print(reverse_number(n5))

    # Problem 6: Sum of digits
    n6: int = int(input())
    print(sum_digits(n6))

    # Problem 7: Multiply two numbers
    a: int = int(input())
    b: int = int(input())
    print(multiply(a, b))


if __name__ == "__main__":
    main()