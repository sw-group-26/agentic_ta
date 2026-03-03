"""HW3 Solution: Loops and Iteration.
Implements loop-based algorithms using while loops.
"""


def sum_of_natural_numbers(n: int) -> int:
    """Sum 1 + 2 + ... + n using a while loop."""
    total: int = 0
    i: int = 1
    while i <= n:
        total += i
        i += 1
    return total


def compute_factorial(n: int) -> int:
    """Compute n! iteratively."""
    result: int = 1
    i: int = 1
    while i <= n:
        result *= i
        i += 1
    return result

def get_fibonacci(n: int) -> int:
    """Get the nth Fibonacci number (1-indexed)."""
    if n <= 2:
        return 1
    prev: int = 1
    curr: int = 1
    count: int = 2
    while count < n:
        prev, curr = curr, prev + curr
        count += 1
    return curr


def digit_count(number: int) -> int:
    """Count digits in a positive integer."""
    count: int = 0
    while number > 0:
        number //= 10
        count += 1
    return count

def reverse_digits(number: int) -> int:
    """Reverse the digits of a number."""
    result: int = 0
    while number > 0:
        result = result * 10 + number % 10
        number //= 10
    return result

def digit_sum(number: int) -> int:
    """Sum all digits of a number."""
    total: int = 0
    while number > 0:
        total += number % 10
        number //= 10
    return total


def loop_multiply(a: int, b: int) -> int:
    """Multiply using repeated addition."""
    product: int = 0
    i: int = 0
    while i < b:
        product += a
        i += 1
    return product


def main() -> None:
    """Run all problems."""
    print(sum_of_natural_numbers(int(input())))
    print(compute_factorial(int(input())))
    print(get_fibonacci(int(input())))
    print(digit_count(int(input())))
    print(reverse_digits(int(input())))
    print(digit_sum(int(input())))
    a: int = int(input())
    b: int = int(input())
    print(loop_multiply(a, b))

if __name__ == "__main__":
    main()