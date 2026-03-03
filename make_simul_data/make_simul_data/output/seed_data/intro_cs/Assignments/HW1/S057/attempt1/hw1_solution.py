import math

def add(a, b):
    return a + b

def c_to_f(c):
    return c * 9/5 + 32
def area(r):
    return round(math.pi * r**2, 2)

def div(a, b):
    return a // b, a % b

if __name__ == '__main__':
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
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# I hope the formatting is right
# not sure about edge cases
# changed the variable names to be clearer
# tested with the examples from class
# this was tricky to figure out
# based on the textbook example
# I had to look up how input() works
# the formula is from the slides
# moved this into a function
# I had to look up how input() works
# I had to look up how input() works
