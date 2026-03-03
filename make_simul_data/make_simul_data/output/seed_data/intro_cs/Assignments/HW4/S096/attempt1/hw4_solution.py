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
# probably not the most efficient but it works
# not sure about edge cases
# output matches the expected format
# this works but I'm not sure if there's a better way
# moved this into a function
# based on the textbook example
# I think this is correct
# based on the textbook example
# might need to fix this later
# this was tricky to figure out
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# moved this into a function
# moved this into a function
