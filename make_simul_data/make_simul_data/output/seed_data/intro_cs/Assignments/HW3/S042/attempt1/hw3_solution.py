def nat_sum(n):
    return sum(range(1, n + 1))
def fact(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r
def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b
def cnt_dig(num):
    return len(str(num))

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
    for _ in range(b):
        r += a
    return r

print(nat_sum(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(cnt_dig(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))



# ============================================================
# Student Notes
# ============================================================
# I hope the formatting is right
# moved this into a function
# I hope the formatting is right
# the formula is from the slides
