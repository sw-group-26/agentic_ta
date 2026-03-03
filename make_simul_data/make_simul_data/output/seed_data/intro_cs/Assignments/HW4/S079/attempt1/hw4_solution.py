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
# asked TA about this part
# this was tricky to figure out
# I think this is correct
# output matches the expected format
# the formula is from the slides
# I had to look up how input() works
# could probably simplify this
# might need to fix this later
# asked TA about this part
# based on the textbook example
# asked TA about this part
# not sure about edge cases
# this was tricky to figure out
# this works but I'm not sure if there's a better way
# changed the variable names to be clearer
