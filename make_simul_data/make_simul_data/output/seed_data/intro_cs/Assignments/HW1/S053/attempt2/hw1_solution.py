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
# based on the textbook example
# this part took me a while
# fixed a bug where it was giving wrong answers
# output matches the expected format
# might need to fix this later
# tested with the examples from class
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# output matches the expected format
# changed the variable names to be clearer
# could probably simplify this
# the formula is from the slides
# the formula is from the slides
