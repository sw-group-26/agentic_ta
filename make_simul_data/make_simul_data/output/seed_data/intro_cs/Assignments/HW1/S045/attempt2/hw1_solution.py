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
# I hope the formatting is right
# could probably simplify this
# not sure about edge cases
# the formula is from the slides
# this part took me a while
# I hope the formatting is right
# moved this into a function
# this was tricky to figure out
# tried a different approach first but this is simpler
# the formula is from the slides
# might need to fix this later
# this part took me a while
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
