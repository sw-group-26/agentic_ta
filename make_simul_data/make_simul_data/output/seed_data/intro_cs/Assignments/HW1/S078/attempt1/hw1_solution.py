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
# based on the textbook example
# asked TA about this part
# this part took me a while
# output matches the expected format
# works for the test cases given
# asked TA about this part
# asked TA about this part
# I hope the formatting is right
# not sure about edge cases
# based on the textbook example
# output matches the expected format
# might need to fix this later
# probably not the most efficient but it works
