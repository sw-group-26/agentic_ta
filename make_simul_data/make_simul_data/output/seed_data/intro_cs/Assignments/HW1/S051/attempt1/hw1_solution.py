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
# asked TA about this part
# I hope the formatting is right
# I hope the formatting is right
# asked TA about this part
# asked TA about this part
# moved this into a function
# moved this into a function
# based on the textbook example
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# probably not the most efficient but it works
