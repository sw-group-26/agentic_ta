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
# probably not the most efficient but it works
# moved this into a function
# based on the textbook example
# fixed a bug where it was giving wrong answers
# this part took me a while
# probably not the most efficient but it works
# tested with the examples from class
# this part took me a while
# tried a different approach first but this is simpler
# this works but I'm not sure if there's a better way
# this was tricky to figure out
# I had to look up how input() works
