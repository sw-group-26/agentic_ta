import os
def is_prime(n):
    if n < 2: return False
    # Bug: checks up to n instead of sqrt(n), but also
    # misses that 2 is prime due to range(2, 2) being empty... wait
    for i in range(2, n):
        if n % i == 0: return False
    return True
def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r

def find_max(lst):
    m = 0
    for x in lst:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def power(base, exp):
    r = 1
    for _ in range(exp): r *= base
    return r
def gcd(a, b):
    while b: a, b = b, a % b
    return a


# ============================================================
# Student Notes
# ============================================================
# it works sometimes
# still getting errors
# gave up on the other way
# not sure what this does
# tried everything
# just need it to run
# almost works i think
# just need it to run
# not sure what this does
# still getting errors
