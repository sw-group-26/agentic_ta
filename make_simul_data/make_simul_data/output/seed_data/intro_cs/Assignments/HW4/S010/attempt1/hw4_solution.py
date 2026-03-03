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
# this works but I'm not sure if there's a better way
# this part took me a while
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# might need to fix this later
# probably not the most efficient but it works
# I had to look up how input() works
# asked TA about this part
# this was tricky to figure out
# I think this is correct
# works for the test cases given
# output matches the expected format
# I think this is correct
