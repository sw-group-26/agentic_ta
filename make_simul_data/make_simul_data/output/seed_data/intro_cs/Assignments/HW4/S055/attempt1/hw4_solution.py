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
# works for the test cases given
# I hope the formatting is right
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# output matches the expected format
# this was tricky to figure out
# not sure about edge cases
# asked TA about this part
# this works but I'm not sure if there's a better way
# changed the variable names to be clearer
# changed the variable names to be clearer
