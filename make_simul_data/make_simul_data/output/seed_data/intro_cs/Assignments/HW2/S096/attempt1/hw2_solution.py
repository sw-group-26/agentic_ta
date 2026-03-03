def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return "F"

def leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False

score = int(input())
print(grade(score))
year = int(input())
print(leap(year))



# ============================================================
# Student Notes
# ============================================================
# this part took me a while
# probably not the most efficient but it works
# not sure about edge cases
# could probably simplify this
# changed the variable names to be clearer
# this part took me a while
# works for the test cases given
# asked TA about this part
# I hope the formatting is right
# I think this is correct
# the formula is from the slides
# works for the test cases given
# I think this is correct
# the formula is from the slides
