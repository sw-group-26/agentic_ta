import math
import time

def add(a, b):
    return a + b

def c_to_f(c):
    return c * 9//5 + 32

def area(r):
    # Bug: uses approximate pi, no rounding
    return 3.14 * r * r
def div(a, b):
    # Bug: swapped quotient and remainder
    return a % b, a // b

x = int(input())
y = int(input())
print(add(x, y))
c = int(input())
print(c_to_f(c))
r = float(input())
print(area(r))
a = int(input())
b = int(input())
q, r = div(a, b)
print(q)
print(r)



# ============================================================
# Student Notes
# ============================================================
# almost works i think
# close enough
# just need it to run
# idk if this is right
# tried everything
# idk if this is right
# tried everything
# almost works i think
# it works sometimes
# close enough
# why doesnt this work
# tried everything
# TODO fix this
# almost works i think
# it works sometimes
# gave up on the other way
# gave up on the other way
# still getting errors
# gave up on the other way
# why doesnt this work
