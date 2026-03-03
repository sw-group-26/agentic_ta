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
# I think this is correct
# works for the test cases given
# this part took me a while
# I hope the formatting is right
# the formula is from the slides
# not sure about edge cases
# this works but I'm not sure if there's a better way
# could probably simplify this
# output matches the expected format
# I hope the formatting is right
# could probably simplify this
# might need to fix this later
# this was tricky to figure out
# the formula is from the slides
