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
# asked TA about this part
# could probably simplify this
# asked TA about this part
# works for the test cases given
# fixed a bug where it was giving wrong answers
# tested with the examples from class
# the formula is from the slides
# this part took me a while
# this works but I'm not sure if there's a better way
# this works but I'm not sure if there's a better way
# tried a different approach first but this is simpler
# moved this into a function
# fixed a bug where it was giving wrong answers
# this part took me a while
# tested with the examples from class
