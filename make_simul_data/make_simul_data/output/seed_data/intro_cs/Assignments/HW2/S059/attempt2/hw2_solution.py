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
# changed the variable names to be clearer
# could probably simplify this
# this part took me a while
# works for the test cases given
# the formula is from the slides
# the formula is from the slides
# changed the variable names to be clearer
# changed the variable names to be clearer
# the formula is from the slides
# tried a different approach first but this is simpler
# I think this is correct
# tested with the examples from class
# this was tricky to figure out
# might need to fix this later
# fixed a bug where it was giving wrong answers
