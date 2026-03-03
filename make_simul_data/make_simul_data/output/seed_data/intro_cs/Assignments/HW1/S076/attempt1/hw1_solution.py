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
# changed the variable names to be clearer
# output matches the expected format
# works for the test cases given
# asked TA about this part
# the formula is from the slides
# not sure about edge cases
# tried a different approach first but this is simpler
# I think this is correct
# might need to fix this later
# I hope the formatting is right
# I hope the formatting is right
# based on the textbook example
# could probably simplify this
# based on the textbook example
# tested with the examples from class
