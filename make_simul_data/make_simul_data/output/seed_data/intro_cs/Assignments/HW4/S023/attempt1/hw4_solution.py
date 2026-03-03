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
# not sure about edge cases
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# could probably simplify this
# not sure about edge cases
# output matches the expected format
# this was tricky to figure out
# the formula is from the slides
# moved this into a function
# the formula is from the slides
# tried a different approach first but this is simpler
# the formula is from the slides
