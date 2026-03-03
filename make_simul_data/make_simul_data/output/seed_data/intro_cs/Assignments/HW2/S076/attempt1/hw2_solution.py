def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return 'B'
    elif s >= 70:
        return 'C'
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
# might need to fix this later
# tried a different approach first but this is simpler
# this part took me a while
# I think this is correct
# works for the test cases given
# might need to fix this later
# not sure about edge cases
# asked TA about this part
# not sure about edge cases
# tested with the examples from class
# I hope the formatting is right
# this was tricky to figure out
# works for the test cases given
# tested with the examples from class
# I hope the formatting is right
# this works but I'm not sure if there's a better way
