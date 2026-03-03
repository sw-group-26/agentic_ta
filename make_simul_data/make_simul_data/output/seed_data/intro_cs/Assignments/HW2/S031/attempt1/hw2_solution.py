def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    elif s >= 60:
        return 'D'
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
# this was tricky to figure out
# this part took me a while
# probably not the most efficient but it works
# output matches the expected format
# changed the variable names to be clearer
# this part took me a while
# asked TA about this part
# fixed a bug where it was giving wrong answers
# the formula is from the slides
# the formula is from the slides
# asked TA about this part
# this part took me a while
# not sure about edge cases
# tested with the examples from class
# probably not the most efficient but it works
# tried a different approach first but this is simpler
