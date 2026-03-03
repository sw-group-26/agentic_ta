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
# moved this into a function
# not sure about edge cases
# probably not the most efficient but it works
# I hope the formatting is right
# I think this is correct
# could probably simplify this
# this part took me a while
# moved this into a function
# asked TA about this part
# changed the variable names to be clearer
# works for the test cases given
# I hope the formatting is right
# output matches the expected format
# this works but I'm not sure if there's a better way
