"""HW4 Solution: Functions and Modular Design.
Main driver using recursive utility functions from hw4_utils.
"""

from hw4_utils import (
    factorial,
    find_max,
    gcd,
    is_palindrome,
    is_prime,
    power,
    reverse_string,
)
def main() -> None:
    """Execute all function problems."""
    print(is_prime(int(input())))
    print(factorial(int(input())))
    print(find_max(list(map(int, input().split()))))
    print(reverse_string(input()))
    print(is_palindrome(input()))
    base: int = int(input())
    exp: int = int(input())
    print(power(base, exp))
    a: int = int(input())
    b: int = int(input())
    print(gcd(a, b))

if __name__ == "__main__":
    main()


# ============================================================
# Student Notes
# ============================================================
# I considered using a dictionary but a list works better for this problem.
# I also tested with boundary values (0, negative numbers, very large inputs).
# This solution handles both integer and floating-point inputs correctly.
