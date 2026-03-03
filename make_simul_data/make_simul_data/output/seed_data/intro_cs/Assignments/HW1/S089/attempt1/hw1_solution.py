import math

def add(a, b):
    return a + b
def c_to_f(c):
    return c * 9//5 + 32

def area(r):
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
# it works sometimes
# close enough
# changed from last version
# still getting errors
# it works sometimes
# TODO fix this
# gave up on the other way
# help
# close enough
# still getting errors
# why doesnt this work
# idk if this is right
# still getting errors
# not sure what this does
# still getting errors
# gave up on the other way
# not sure what this does
# gave up on the other way
# still getting errors
# why doesnt this work
# idk if this is right
# fix later
# just need it to run
