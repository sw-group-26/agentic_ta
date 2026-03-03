"""HW4 Solution: Functions and Modular Design.
This module serves as the main driver that reads input and calls
utility functions defined in hw4_utils.py.
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
    """Run all function-based problems."""
    # Problem 1-2: Primality check
    n: int = int(input())
    print(is_prime(n))

    # Problem 3: Factorial
    n = int(input())
    print(factorial(n))

    # Problem 4: Find maximum in a list
    nums: list[int] = list(map(int, input().split()))
    print(find_max(nums))

    # Problem 5: Reverse string
    text: str = input()
    print(reverse_string(text))

    # Problem 6: Palindrome check
    text = input()
    print(is_palindrome(text))

    # Problem 7: Power
    base: int = int(input())
    exp: int = int(input())
    print(power(base, exp))
    # Problem 8: GCD
    a: int = int(input())
    b: int = int(input())
    print(gcd(a, b))
if __name__ == "__main__":
    main()
