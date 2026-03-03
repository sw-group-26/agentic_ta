import math

def add(a, b):
    return a + b

def c_to_f(c):
    return c * 9/5 + 32

def area(r):
    return round(math.pi * r**2, 2)

def div(a, b):
    return a // b, a % b
if __name__ == "__main__":
    x = int(input())
    y = int(input())
    print(add(x, y))

    c = float(input())
    print(c_to_f(c))

    r = float(input())
    print(area(r))

    a = int(input())
    b = int(input())
    q, rem = div(a, b)
    print(q)
    print(rem)



# ============================================================
# Student Notes
# ============================================================
# not sure about edge cases
# this works but I'm not sure if there's a better way
# tried a different approach first but this is simpler
# tried a different approach first but this is simpler
# works for the test cases given
# tried a different approach first but this is simpler
# I had to look up how input() works
# tested with the examples from class
# the formula is from the slides
# could probably simplify this
# tested with the examples from class
