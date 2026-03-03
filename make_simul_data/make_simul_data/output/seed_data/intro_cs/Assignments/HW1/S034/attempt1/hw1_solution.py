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
# this part took me a while
# moved this into a function
# asked TA about this part
# might need to fix this later
# output matches the expected format
# works for the test cases given
# the formula is from the slides
# might need to fix this later
# not sure about edge cases
# I had to look up how input() works
# asked TA about this part
# could probably simplify this
# could probably simplify this
# could probably simplify this
# I had to look up how input() works
# works for the test cases given
