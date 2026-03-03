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
# this part took me a while
# changed the variable names to be clearer
# could probably simplify this
# could probably simplify this
# asked TA about this part
# I had to look up how input() works
# tried a different approach first but this is simpler
# tried a different approach first but this is simpler
# based on the textbook example
# based on the textbook example
# not sure about edge cases
# works for the test cases given
# works for the test cases given
