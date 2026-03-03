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

if __name__ == "__main__":
    do_add()
    do_convert()
    do_area()
    do_div()



# ============================================================
# Student Notes
# ============================================================
# tested with the examples from class
# not sure about edge cases
# works for the test cases given
# asked TA about this part
# I hope the formatting is right
# changed the variable names to be clearer
# tested with the examples from class
# tested with the examples from class
# fixed a bug where it was giving wrong answers
# output matches the expected format
# changed the variable names to be clearer
# I think this is correct
# asked TA about this part
# this works but I'm not sure if there's a better way
