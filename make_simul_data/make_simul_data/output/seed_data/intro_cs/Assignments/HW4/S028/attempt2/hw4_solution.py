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
# might need to fix this later
# I think this is correct
# I had to look up how input() works
# could probably simplify this
# tested with the examples from class
# I think this is correct
# I think this is correct
# tried a different approach first but this is simpler
# asked TA about this part
# fixed a bug where it was giving wrong answers
# moved this into a function
# this was tricky to figure out
# might need to fix this later
# probably not the most efficient but it works
