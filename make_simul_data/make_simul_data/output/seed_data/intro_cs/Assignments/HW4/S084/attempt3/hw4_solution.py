from hw4_utils import *

print(is_prime(int(input())))
print(factorial(int(input())))
nums = list(map(int, input().split()))
print(find_max(nums))
print(reverse_string(input()))
print(is_palindrome(input()))
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
# I had to look up how input() works
# fixed a bug where it was giving wrong answers
# based on the textbook example
# tried a different approach first but this is simpler
# could probably simplify this
# probably not the most efficient but it works
# this works but I'm not sure if there's a better way
# works for the test cases given
# the formula is from the slides
# works for the test cases given
# based on the textbook example
# I think this is correct
# might need to fix this later
# I think this is correct
# changed the variable names to be clearer
