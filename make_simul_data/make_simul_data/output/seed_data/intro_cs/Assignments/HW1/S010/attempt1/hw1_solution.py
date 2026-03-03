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
# this was tricky to figure out
# this was tricky to figure out
# probably not the most efficient but it works
# moved this into a function
# might need to fix this later
# probably not the most efficient but it works
# tested with the examples from class
# this works but I'm not sure if there's a better way
# this part took me a while
# might need to fix this later
# I hope the formatting is right
# based on the textbook example
