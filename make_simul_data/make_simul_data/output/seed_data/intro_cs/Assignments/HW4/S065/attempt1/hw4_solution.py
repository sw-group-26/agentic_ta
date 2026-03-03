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
# not sure about edge cases
# this part took me a while
# could probably simplify this
# asked TA about this part
# works for the test cases given
# could probably simplify this
# fixed a bug where it was giving wrong answers
# might need to fix this later
# could probably simplify this
# the formula is from the slides
# I had to look up how input() works
# the formula is from the slides
# output matches the expected format
# changed the variable names to be clearer
