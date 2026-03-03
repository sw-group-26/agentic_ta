def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    elif s >= 60:
        return "D"
    else:
        return "F"

def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))


# ============================================================
# Student Notes
# ============================================================
# works for the test cases given
# works for the test cases given
# I had to look up how input() works
# moved this into a function
# this was tricky to figure out
# fixed a bug where it was giving wrong answers
# could probably simplify this
# I hope the formatting is right
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
# probably not the most efficient but it works
# changed the variable names to be clearer
# tried a different approach first but this is simpler
# might need to fix this later
