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
# I think this is correct
# I hope the formatting is right
# this works but I'm not sure if there's a better way
# I think this is correct
# fixed a bug where it was giving wrong answers
# tested with the examples from class
# moved this into a function
# tested with the examples from class
# I think this is correct
# I hope the formatting is right
# changed the variable names to be clearer
# output matches the expected format
