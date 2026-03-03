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
# the formula is from the slides
# tested with the examples from class
# tried a different approach first but this is simpler
# works for the test cases given
# this was tricky to figure out
# moved this into a function
# tested with the examples from class
# I think this is correct
# probably not the most efficient but it works
# not sure about edge cases
# changed the variable names to be clearer
# output matches the expected format
# output matches the expected format
