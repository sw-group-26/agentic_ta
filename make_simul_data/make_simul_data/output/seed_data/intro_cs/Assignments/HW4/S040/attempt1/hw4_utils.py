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
# fix later
# still getting errors
# changed from last version
# TODO fix this
# not sure what this does
# it works sometimes
# this keeps breaking
# not sure what this does
# not sure what this does
# idk if this is right
# still getting errors
# TODO fix this
# almost works i think
# fix later
# not sure what this does
# still getting errors
