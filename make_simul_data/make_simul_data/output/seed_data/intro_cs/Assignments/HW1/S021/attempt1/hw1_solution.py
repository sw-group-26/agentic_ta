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
# changed the variable names to be clearer
# might need to fix this later
# I had to look up how input() works
# based on the textbook example
# I hope the formatting is right
# tried a different approach first but this is simpler
# this works but I'm not sure if there's a better way
# works for the test cases given
# output matches the expected format
# I had to look up how input() works
# changed the variable names to be clearer
# asked TA about this part
# fixed a bug where it was giving wrong answers
