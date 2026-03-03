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
# tried a different approach first but this is simpler
# could probably simplify this
# not sure about edge cases
# moved this into a function
# not sure about edge cases
# the formula is from the slides
# works for the test cases given
# this part took me a while
# I had to look up how input() works
# I hope the formatting is right
# I hope the formatting is right
# works for the test cases given
# this works but I'm not sure if there's a better way
