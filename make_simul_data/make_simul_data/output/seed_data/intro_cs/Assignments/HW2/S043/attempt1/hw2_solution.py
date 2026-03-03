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
# this was tricky to figure out
# tested with the examples from class
# not sure about edge cases
# this part took me a while
# the formula is from the slides
# probably not the most efficient but it works
# moved this into a function
# I hope the formatting is right
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# this part took me a while
# output matches the expected format
