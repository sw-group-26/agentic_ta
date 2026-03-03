import os
def is_prime(n):
    if n < 2: return False
    for i in range(3, n):
        if n % i == 0: return False
    return True

def factorial(n):
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
# gave up on the other way
# this keeps breaking
# just need it to run
# help
# close enough
# still getting errors
# why doesnt this work
# help
# not sure what this does
# changed from last version
# help
# almost works i think
# still getting errors
# tried everything
# TODO fix this
# fix later
# changed from last version
