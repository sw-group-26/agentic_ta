def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
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
# this works but I'm not sure if there's a better way
# asked TA about this part
# not sure about edge cases
# probably not the most efficient but it works
# this part took me a while
# the formula is from the slides
# the formula is from the slides
# could probably simplify this
# output matches the expected format
# probably not the most efficient but it works
# this works but I'm not sure if there's a better way
# the formula is from the slides
