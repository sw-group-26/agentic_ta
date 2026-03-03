def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def find_max(nums):
    m = nums[0]
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
# changed the variable names to be clearer
# tested with the examples from class
# I hope the formatting is right
# the formula is from the slides
# not sure about edge cases
# tried a different approach first but this is simpler
# might need to fix this later
# could probably simplify this
# tested with the examples from class
