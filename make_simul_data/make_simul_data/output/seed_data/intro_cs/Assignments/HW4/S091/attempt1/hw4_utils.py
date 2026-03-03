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
# fixed a bug where it was giving wrong answers
# not sure about edge cases
# the formula is from the slides
# I had to look up how input() works
# might need to fix this later
# fixed a bug where it was giving wrong answers
# I hope the formatting is right
# asked TA about this part
# I think this is correct
# probably not the most efficient but it works
