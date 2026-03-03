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
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
# this part took me a while
# the formula is from the slides
# based on the textbook example
# output matches the expected format
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# asked TA about this part
# moved this into a function
# fixed a bug where it was giving wrong answers
