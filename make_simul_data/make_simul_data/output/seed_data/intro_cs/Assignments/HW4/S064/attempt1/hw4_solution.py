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
# moved this into a function
# asked TA about this part
# I think this is correct
# fixed a bug where it was giving wrong answers
# I think this is correct
# based on the textbook example
# changed the variable names to be clearer
# this was tricky to figure out
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# moved this into a function
# I think this is correct
# this works but I'm not sure if there's a better way
# this part took me a while
