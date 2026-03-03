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
# I had to look up how input() works
# this part took me a while
# works for the test cases given
# this works but I'm not sure if there's a better way
# not sure about edge cases
# tested with the examples from class
# works for the test cases given
# tested with the examples from class
# probably not the most efficient but it works
