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
# not sure about edge cases
# I had to look up how input() works
# I had to look up how input() works
# asked TA about this part
# could probably simplify this
# this part took me a while
# tried a different approach first but this is simpler
# not sure about edge cases
# might need to fix this later
# not sure about edge cases
# works for the test cases given
# asked TA about this part
# tested with the examples from class
# based on the textbook example
