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
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# moved this into a function
# asked TA about this part
# not sure about edge cases
# asked TA about this part
# output matches the expected format
# fixed a bug where it was giving wrong answers
# this works but I'm not sure if there's a better way
# the formula is from the slides
# this part took me a while
# this was tricky to figure out
