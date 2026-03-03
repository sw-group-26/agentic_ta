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
# I had to look up how input() works
# might need to fix this later
# works for the test cases given
# I think this is correct
# tested with the examples from class
# could probably simplify this
# moved this into a function
# might need to fix this later
# the formula is from the slides
# this part took me a while
# this was tricky to figure out
# I had to look up how input() works
# this part took me a while
# output matches the expected format
