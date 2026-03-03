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
# this part took me a while
# asked TA about this part
# this part took me a while
# output matches the expected format
# works for the test cases given
# output matches the expected format
# might need to fix this later
# moved this into a function
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# output matches the expected format
# works for the test cases given
# tried a different approach first but this is simpler
