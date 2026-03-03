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
# might need to fix this later
# tried a different approach first but this is simpler
# asked TA about this part
# probably not the most efficient but it works
# could probably simplify this
# tested with the examples from class
# this was tricky to figure out
# might need to fix this later
# output matches the expected format
# I hope the formatting is right
# I hope the formatting is right
# tried a different approach first but this is simpler
