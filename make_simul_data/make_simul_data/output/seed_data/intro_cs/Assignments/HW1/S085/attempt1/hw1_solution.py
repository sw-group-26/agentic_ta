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
# the formula is from the slides
# not sure about edge cases
# this part took me a while
# I had to look up how input() works
# I hope the formatting is right
# fixed a bug where it was giving wrong answers
# could probably simplify this
# works for the test cases given
# asked TA about this part
# I think this is correct
# this works but I'm not sure if there's a better way
# I had to look up how input() works
# fixed a bug where it was giving wrong answers
# could probably simplify this
