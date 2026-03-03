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
        return 'F'

def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))


# ============================================================
# Student Notes
# ============================================================
# moved this into a function
# probably not the most efficient but it works
# not sure about edge cases
# output matches the expected format
# moved this into a function
# the formula is from the slides
# works for the test cases given
# this works but I'm not sure if there's a better way
# could probably simplify this
# the formula is from the slides
# tried a different approach first but this is simpler
# based on the textbook example
# works for the test cases given
# works for the test cases given
# not sure about edge cases
# based on the textbook example
