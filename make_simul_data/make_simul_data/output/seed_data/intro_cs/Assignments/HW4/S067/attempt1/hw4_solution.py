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
# based on the textbook example
# I had to look up how input() works
# asked TA about this part
# might need to fix this later
# I hope the formatting is right
# output matches the expected format
# asked TA about this part
# might need to fix this later
# tried a different approach first but this is simpler
# output matches the expected format
# I think this is correct
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# works for the test cases given
