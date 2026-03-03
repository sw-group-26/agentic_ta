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
# the formula is from the slides
# moved this into a function
# changed the variable names to be clearer
# based on the textbook example
# tried a different approach first but this is simpler
# the formula is from the slides
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# this works but I'm not sure if there's a better way
# this was tricky to figure out
# I hope the formatting is right
# could probably simplify this
