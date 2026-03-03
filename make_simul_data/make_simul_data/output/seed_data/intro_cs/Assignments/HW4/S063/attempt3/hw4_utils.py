def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0: return False
    i = 3
    while i * i <= n:
        if n % i == 0: return False
        i += 2
    return True

def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r

def find_max(lst):
    m = lst[0]
    for x in lst[1:]:
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
# I think this is correct
# might need to fix this later
# tested with the examples from class
# tried a different approach first but this is simpler
# asked TA about this part
# works for the test cases given
# output matches the expected format
# might need to fix this later
