"""HW4 Solution: Functions and Modular Design.

Driver module that imports utilities from hw4_utils and
processes input for each problem.
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
    """Process all function problems."""
    # Primality test
    print(is_prime(int(input())))

    # Factorial
    print(factorial(int(input())))

    # Find max in list
    numbers: list[int] = list(map(int, input().split()))
    print(find_max(numbers))
    # Reverse string
    print(reverse_string(input()))
    # Palindrome check
    print(is_palindrome(input()))

    # Power
    b: int = int(input())
    e: int = int(input())
    print(power(b, e))

    # GCD
    x: int = int(input())
    y: int = int(input())
    print(gcd(x, y))


if __name__ == "__main__":
    main()



# ============================================================
# Student Notes
# ============================================================
# The logic was derived from the examples discussed in class.
