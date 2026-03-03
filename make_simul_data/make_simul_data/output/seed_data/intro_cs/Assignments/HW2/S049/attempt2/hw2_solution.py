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
# this works but I'm not sure if there's a better way
# could probably simplify this
# works for the test cases given
# I had to look up how input() works
# the formula is from the slides
# this was tricky to figure out
# tried a different approach first but this is simpler
# tested with the examples from class
# could probably simplify this
# this was tricky to figure out
# tried a different approach first but this is simpler
