def get_grade(s):
    if s >= 90:
        return 'A'
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
# output matches the expected format
# probably not the most efficient but it works
# changed the variable names to be clearer
# the formula is from the slides
# this works but I'm not sure if there's a better way
# might need to fix this later
# tested with the examples from class
# asked TA about this part
# I hope the formatting is right
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# I had to look up how input() works
# probably not the most efficient but it works
# this was tricky to figure out
