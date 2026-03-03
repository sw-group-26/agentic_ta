import sys
def is_prime(n):
    if n < 2: return False
    for i in range(3, n):
        if n % i == 0: return False
    return True

def factorial(n):
    # Bug: returns 0 for n=0 or n=1 because range(2,1) is empty
    result = 0
    for i in range(2, n + 1):
        result *= i
    return result

def find_max(nums):
    m = 0
    for x in nums:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]
def power(b, e):
    r = 1
    for _ in range(e):
        r *= b
    return r

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a



# ============================================================
# Student Notes
# ============================================================
# still getting errors
# still getting errors
# not sure what this does
# changed from last version
# this keeps breaking
# help
# still getting errors
# tried everything
# it works sometimes
# close enough
# just need it to run
# why doesnt this work
# gave up on the other way
