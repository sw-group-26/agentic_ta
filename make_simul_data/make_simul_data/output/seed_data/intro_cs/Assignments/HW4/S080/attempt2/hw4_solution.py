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
# I think this is correct
# output matches the expected format
# changed the variable names to be clearer
# based on the textbook example
# the formula is from the slides
# changed the variable names to be clearer
# tested with the examples from class
# tried a different approach first but this is simpler
# not sure about edge cases
# changed the variable names to be clearer
# I think this is correct
# could probably simplify this
# not sure about edge cases
# based on the textbook example
