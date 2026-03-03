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
# tested with the examples from class
# I think this is correct
# I had to look up how input() works
# output matches the expected format
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# asked TA about this part
# this part took me a while
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
# this was tricky to figure out
# probably not the most efficient but it works
# could probably simplify this
