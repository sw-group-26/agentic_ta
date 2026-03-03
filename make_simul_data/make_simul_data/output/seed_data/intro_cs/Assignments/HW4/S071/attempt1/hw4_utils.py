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
# fixed a bug where it was giving wrong answers
# tested with the examples from class
# fixed a bug where it was giving wrong answers
# tried a different approach first but this is simpler
# I think this is correct
# asked TA about this part
# might need to fix this later
# could probably simplify this
