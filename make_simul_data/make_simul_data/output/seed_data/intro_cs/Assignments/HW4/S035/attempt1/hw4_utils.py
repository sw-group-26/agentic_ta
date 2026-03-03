import sys
def is_prime(n):
    if n < 2: return False
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
    # Bug: wrong order of arguments in recursive call
    if b == 0: return a
    return gcd(a % b, b)



# ============================================================
# Student Notes
# ============================================================
# changed from last version
# why doesnt this work
# this keeps breaking
# fix later
# this keeps breaking
# fix later
# changed from last version
# not sure what this does
# tried everything
# still getting errors
# fix later
# fix later
# changed from last version
# almost works i think
# gave up on the other way
# fix later
# tried everything
