"""HW3 Solution: Loops and Iteration.

A clean implementation using for-loops and while-loops
for various numeric algorithms.
"""


def natural_sum(n: int) -> int:
    """Return the sum of integers from 1 to n."""
    return sum(range(1, n + 1))


def factorial(n: int) -> int:
    """Return n factorial computed iteratively."""
    result: int = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (1-indexed)."""
    if n <= 2:
        return 1
    a: int = 1
    b: int = 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b


def count_digits(num: int) -> int:
    """Count digits by converting to string."""
    return len(str(num))

def reverse_number(num: int) -> int:
    """Reverse digits using modular arithmetic."""
    result: int = 0
    while num > 0:
        result = result * 10 + num % 10
        num //= 10
    return result


def digit_sum(num: int) -> int:
    """Sum of all digits in a number."""
    total: int = 0
    while num > 0:
        total += num % 10
        num //= 10
    return total

def repeated_add(a: int, b: int) -> int:
    """Multiply via repeated addition."""
    result: int = 0
    for _ in range(b):
        result += a
    return result


def main() -> None:
    """Execute all loop problems in order."""
    print(natural_sum(int(input())))
    print(factorial(int(input())))
    print(fibonacci(int(input())))
    print(count_digits(int(input())))
    print(reverse_number(int(input())))
    print(digit_sum(int(input())))
    a: int = int(input())
    b: int = int(input())
    print(repeated_add(a, b))

if __name__ == "__main__":
    main()