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
# fix later
# it works sometimes
# it works sometimes
# close enough
# changed from last version
# why doesnt this work
# gave up on the other way
# help
# help
# gave up on the other way
# why doesnt this work
# TODO fix this
# close enough
# help
# close enough
# still getting errors
# almost works i think
# gave up on the other way
# just need it to run
# this keeps breaking
