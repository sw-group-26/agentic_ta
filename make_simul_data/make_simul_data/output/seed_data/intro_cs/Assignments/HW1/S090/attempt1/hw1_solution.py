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
# this was tricky to figure out
# I think this is correct
# output matches the expected format
# probably not the most efficient but it works
# the formula is from the slides
# probably not the most efficient but it works
# asked TA about this part
# tested with the examples from class
# based on the textbook example
# asked TA about this part
# I had to look up how input() works
# I had to look up how input() works
# tried a different approach first but this is simpler
# output matches the expected format
