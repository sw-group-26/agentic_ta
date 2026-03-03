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
# fixed a bug where it was giving wrong answers
# output matches the expected format
# probably not the most efficient but it works
# I think this is correct
# fixed a bug where it was giving wrong answers
# works for the test cases given
# the formula is from the slides
# probably not the most efficient but it works
# could probably simplify this
# moved this into a function
# asked TA about this part
# not sure about edge cases
# I think this is correct
# tried a different approach first but this is simpler
