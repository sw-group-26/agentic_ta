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
# tested with the examples from class
# I hope the formatting is right
# works for the test cases given
# asked TA about this part
# probably not the most efficient but it works
# changed the variable names to be clearer
# works for the test cases given
# probably not the most efficient but it works
# tested with the examples from class
# probably not the most efficient but it works
# the formula is from the slides
# not sure about edge cases
# output matches the expected format
