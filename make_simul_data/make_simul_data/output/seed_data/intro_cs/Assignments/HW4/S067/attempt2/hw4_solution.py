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
# this was tricky to figure out
# might need to fix this later
# I had to look up how input() works
# this part took me a while
# moved this into a function
# output matches the expected format
# asked TA about this part
# this was tricky to figure out
# could probably simplify this
# output matches the expected format
# tested with the examples from class
# asked TA about this part
# I had to look up how input() works
# the formula is from the slides
