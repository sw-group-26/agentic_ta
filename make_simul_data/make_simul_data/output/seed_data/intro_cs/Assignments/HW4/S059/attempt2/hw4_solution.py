from hw4_utils import (is_prime, factorial, find_max,
    reverse_string, is_palindrome, power, gcd)

n = int(input())
print(is_prime(n))
n = int(input())
print(factorial(n))
nums = list(map(int, input().split()))
print(find_max(nums))
s = input()
print(reverse_string(s))
s = input()
print(is_palindrome(s))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))


# ============================================================
# Student Notes
# ============================================================
# moved this into a function
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# tried a different approach first but this is simpler
# tested with the examples from class
# I had to look up how input() works
# works for the test cases given
# tried a different approach first but this is simpler
# could probably simplify this
# based on the textbook example
# tested with the examples from class
# probably not the most efficient but it works
