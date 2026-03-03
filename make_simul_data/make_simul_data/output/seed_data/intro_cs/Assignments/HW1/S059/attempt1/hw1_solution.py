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
# fixed a bug where it was giving wrong answers
# this part took me a while
# I had to look up how input() works
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# changed the variable names to be clearer
# works for the test cases given
# tested with the examples from class
# the formula is from the slides
# I had to look up how input() works
# tested with the examples from class
# moved this into a function
