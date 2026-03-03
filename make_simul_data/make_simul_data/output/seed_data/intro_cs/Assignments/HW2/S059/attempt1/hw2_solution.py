def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return 'B'
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
# based on the textbook example
# the formula is from the slides
# based on the textbook example
# tested with the examples from class
# this was tricky to figure out
# tested with the examples from class
# I think this is correct
# could probably simplify this
# might need to fix this later
# fixed a bug where it was giving wrong answers
# probably not the most efficient but it works
# this part took me a while
# tested with the examples from class
