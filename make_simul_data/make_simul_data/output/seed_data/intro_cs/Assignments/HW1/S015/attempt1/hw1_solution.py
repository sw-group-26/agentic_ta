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
# tried a different approach first but this is simpler
# tried a different approach first but this is simpler
# works for the test cases given
# probably not the most efficient but it works
# output matches the expected format
# the formula is from the slides
# probably not the most efficient but it works
# I hope the formatting is right
# I had to look up how input() works
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
