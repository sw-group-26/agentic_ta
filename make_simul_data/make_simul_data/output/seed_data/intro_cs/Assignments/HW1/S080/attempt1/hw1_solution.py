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
# tried a different approach first but this is simpler
# this was tricky to figure out
# changed the variable names to be clearer
# output matches the expected format
# works for the test cases given
# tried a different approach first but this is simpler
# I hope the formatting is right
# the formula is from the slides
# I hope the formatting is right
# this works but I'm not sure if there's a better way
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
