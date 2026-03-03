import math

def do_add():
    a = int(input())
    b = int(input())
    print(a + b)

def do_convert():
    c = float(input())
    print(c * 9/5 + 32)

def do_area():
    r = float(input())
    print(round(math.pi * r**2, 2))

def do_div():
    a = int(input())
    b = int(input())
    print(a // b)
    print(a % b)
if __name__ == '__main__':
    do_add()
    do_convert()
    do_area()
    do_div()



# ============================================================
# Student Notes
# ============================================================
# works for the test cases given
# asked TA about this part
# output matches the expected format
# could probably simplify this
# works for the test cases given
# tested with the examples from class
# the formula is from the slides
# I had to look up how input() works
# could probably simplify this
# tested with the examples from class
# changed the variable names to be clearer
# changed the variable names to be clearer
# I had to look up how input() works
# moved this into a function
