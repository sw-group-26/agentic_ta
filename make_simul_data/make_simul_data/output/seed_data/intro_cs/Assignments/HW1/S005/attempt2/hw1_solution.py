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
# I had to look up how input() works
# works for the test cases given
# moved this into a function
# moved this into a function
# output matches the expected format
# based on the textbook example
# I hope the formatting is right
# might need to fix this later
# I hope the formatting is right
# the formula is from the slides
# output matches the expected format
# moved this into a function
# this works but I'm not sure if there's a better way
