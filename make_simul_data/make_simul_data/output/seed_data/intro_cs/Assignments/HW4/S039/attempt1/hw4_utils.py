import sys
def is_prime(n):
    if n < 2: return False
    # Bug: only checks divisibility by 2
    if n % 2 == 0: return False
    return True
def factorial(n):
    if n <= 1: return 1
    return n * factorial(n - 1)
def find_max(nums):
    m = nums[0]
    for x in nums:
        if x > m: m = x
    return m
def reverse_string(s): return s[::-1]
def is_palindrome(s): return s == s[::-1]

def power(b, e):
    if e == 0: return 1
    return b * power(b, e - 1)

def gcd(a, b):
    if b == 0: return a
    return gcd(a % b, b)



# ============================================================
# Student Notes
# ============================================================
# still getting errors
# not sure what this does
# this keeps breaking
# this keeps breaking
# it works sometimes
# just need it to run
# idk if this is right
# changed from last version
# TODO fix this
# changed from last version
# tried everything
# not sure what this does
# tried everything
# not sure what this does
# just need it to run
# it works sometimes
