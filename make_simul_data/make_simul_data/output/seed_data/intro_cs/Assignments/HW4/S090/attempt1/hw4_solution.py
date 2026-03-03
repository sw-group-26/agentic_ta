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
# probably not the most efficient but it works
# not sure about edge cases
# tested with the examples from class
# tried a different approach first but this is simpler
# this part took me a while
# this works but I'm not sure if there's a better way
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# tried a different approach first but this is simpler
# the formula is from the slides
