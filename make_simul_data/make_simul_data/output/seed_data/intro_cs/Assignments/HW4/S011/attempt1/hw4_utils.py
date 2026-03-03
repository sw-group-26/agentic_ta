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
    # Bug: compares against 0 instead of first element
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
# this keeps breaking
# why doesnt this work
# tried everything
# fix later
# it works sometimes
# fix later
# just need it to run
# almost works i think
# just need it to run
# just need it to run
# help
# idk if this is right
# tried everything
# help
# changed from last version
