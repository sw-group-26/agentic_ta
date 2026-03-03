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
        return 'F'
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
# could probably simplify this
# the formula is from the slides
# could probably simplify this
# not sure about edge cases
# could probably simplify this
# this part took me a while
# this works but I'm not sure if there's a better way
# works for the test cases given
# output matches the expected format
# the formula is from the slides
# probably not the most efficient but it works
# I hope the formatting is right
# this part took me a while
