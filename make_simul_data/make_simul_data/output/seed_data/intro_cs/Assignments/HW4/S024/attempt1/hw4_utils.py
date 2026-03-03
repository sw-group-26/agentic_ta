def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0: return False
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
    return gcd(b, a % b)


# ============================================================
# Student Notes
# ============================================================
# probably not the most efficient but it works
# this was tricky to figure out
# this was tricky to figure out
# I hope the formatting is right
# tried a different approach first but this is simpler
# output matches the expected format
# tried a different approach first but this is simpler
# based on the textbook example
