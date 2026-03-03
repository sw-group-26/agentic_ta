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
# might need to fix this later
# this part took me a while
# not sure about edge cases
# probably not the most efficient but it works
# this was tricky to figure out
# works for the test cases given
# could probably simplify this
# asked TA about this part
# the formula is from the slides
# not sure about edge cases
# asked TA about this part
# changed the variable names to be clearer
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
