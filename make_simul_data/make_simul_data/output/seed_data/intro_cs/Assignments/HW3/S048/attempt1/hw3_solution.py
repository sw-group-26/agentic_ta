def sum_n(n):
    total = 0
    i = 1
    while i <= n:
        total += i
        i += 1
    return total

def fact(n):
    result = 1
    i = 1
    while i <= n:
        result *= i
        i += 1
    return result

def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    i = 2
    while i < n:
        a, b = b, a + b
        i += 1
    return b

def digits(num):
    c = 0
    while num > 0:
        num //= 10
        c += 1
    return c
def rev(num):
    r = 0
    while num > 0:
        r = r * 10 + num % 10
        num //= 10
    return r

def dsum(num):
    s = 0
    while num > 0:
        s += num % 10
        num //= 10
    return s

def mul(a, b):
    r = 0
    i = 0
    while i < b:
        r += a
        i += 1
    return r

print(sum_n(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(digits(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))


# ============================================================
# Student Notes
# ============================================================
# I had to look up how input() works
