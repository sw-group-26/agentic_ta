def is_prime(n):
    if n < 2: return False
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
# help
# tried everything
# this keeps breaking
# TODO fix this
# fix later
# not sure what this does
# almost works i think
# fix later
# idk if this is right
# this keeps breaking
# not sure what this does
# fix later
# almost works i think
# tried everything
# just need it to run
# changed from last version
# idk if this is right
# not sure what this does
