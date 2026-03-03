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
# I think this is correct
# output matches the expected format
# fixed a bug where it was giving wrong answers
# might need to fix this later
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# not sure about edge cases
# I think this is correct
# could probably simplify this
# tested with the examples from class
# changed the variable names to be clearer
# changed the variable names to be clearer
