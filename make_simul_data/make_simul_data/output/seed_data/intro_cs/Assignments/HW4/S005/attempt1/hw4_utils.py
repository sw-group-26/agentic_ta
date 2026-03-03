import time
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
    if b == 0: return a
    return gcd(a % b, b)



# ============================================================
# Student Notes
# ============================================================
# TODO fix this
# why doesnt this work
# just need it to run
# TODO fix this
# it works sometimes
# it works sometimes
# TODO fix this
# not sure what this does
# close enough
# idk if this is right
# tried everything
# close enough
# gave up on the other way
# this keeps breaking
# why doesnt this work
# almost works i think
# TODO fix this
# tried everything
# almost works i think
# help
