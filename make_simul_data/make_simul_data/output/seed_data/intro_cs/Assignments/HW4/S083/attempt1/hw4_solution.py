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
# could probably simplify this
# probably not the most efficient but it works
# I had to look up how input() works
# this part took me a while
# works for the test cases given
# works for the test cases given
# output matches the expected format
# not sure about edge cases
# fixed a bug where it was giving wrong answers
# I think this is correct
# not sure about edge cases
# could probably simplify this
# this part took me a while
# probably not the most efficient but it works
