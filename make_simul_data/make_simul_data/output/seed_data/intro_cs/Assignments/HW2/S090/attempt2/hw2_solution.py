def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
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
# works for the test cases given
# could probably simplify this
# this part took me a while
# might need to fix this later
# fixed a bug where it was giving wrong answers
# asked TA about this part
# changed the variable names to be clearer
# the formula is from the slides
# asked TA about this part
# not sure about edge cases
# output matches the expected format
# I hope the formatting is right
# I had to look up how input() works
