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
# I had to look up how input() works
# this works but I'm not sure if there's a better way
# asked TA about this part
# asked TA about this part
# not sure about edge cases
# tested with the examples from class
# not sure about edge cases
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# tested with the examples from class
# I had to look up how input() works
# might need to fix this later
