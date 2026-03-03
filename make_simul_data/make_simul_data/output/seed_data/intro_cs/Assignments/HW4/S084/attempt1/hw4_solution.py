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
# tested with the examples from class
# this was tricky to figure out
# I hope the formatting is right
# changed the variable names to be clearer
# output matches the expected format
# could probably simplify this
# might need to fix this later
# not sure about edge cases
# this works but I'm not sure if there's a better way
# I think this is correct
# I had to look up how input() works
# works for the test cases given
# not sure about edge cases
# based on the textbook example
