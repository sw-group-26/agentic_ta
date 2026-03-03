def sum_n(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total
def fact(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
def fib(n):
    if n <= 2:
        return 1
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b

def count_dig(num):
    count = 0
    while num > 0:
        num //= 10
        count += 1
    return count

def rev_num(num):
    rev = 0
    while num > 0:
        rev = rev * 10 + num % 10
        num //= 10
    return rev

def sum_dig(num):
    total = 0
    while num > 0:
        total += num % 10
        num //= 10
    return total

def mult(a, b):
    result = 0
    for _ in range(b):
        result += a
    return result
n = int(input())
print(sum_n(n))
n = int(input())
print(fact(n))
n = int(input())
print(fib(n))
n = int(input())
print(count_dig(n))
n = int(input())
print(rev_num(n))
n = int(input())
print(sum_dig(n))
a = int(input())
b = int(input())
print(mult(a, b))



# ============================================================
# Student Notes
# ============================================================
# not sure about edge cases
