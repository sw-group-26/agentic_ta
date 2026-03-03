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
# asked TA about this part
# might need to fix this later
# works for the test cases given
# not sure about edge cases
# not sure about edge cases
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# I had to look up how input() works
# tested with the examples from class
