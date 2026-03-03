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
# tested with the examples from class
# probably not the most efficient but it works
# I hope the formatting is right
# I had to look up how input() works
# I think this is correct
# might need to fix this later
# might need to fix this later
# asked TA about this part
# based on the textbook example
# fixed a bug where it was giving wrong answers
# could probably simplify this
# the formula is from the slides
# tested with the examples from class
