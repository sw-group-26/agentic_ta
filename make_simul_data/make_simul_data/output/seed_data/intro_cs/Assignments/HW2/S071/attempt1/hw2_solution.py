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
# based on the textbook example
# output matches the expected format
# I hope the formatting is right
# could probably simplify this
# tested with the examples from class
# not sure about edge cases
# fixed a bug where it was giving wrong answers
# probably not the most efficient but it works
# asked TA about this part
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# probably not the most efficient but it works
# I think this is correct
# this was tricky to figure out
# based on the textbook example
