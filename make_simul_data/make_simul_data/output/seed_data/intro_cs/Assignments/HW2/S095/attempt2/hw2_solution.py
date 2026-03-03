def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
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
# tested with the examples from class
# could probably simplify this
# the formula is from the slides
# might need to fix this later
# could probably simplify this
# moved this into a function
# changed the variable names to be clearer
# probably not the most efficient but it works
# I think this is correct
# moved this into a function
# works for the test cases given
# tried a different approach first but this is simpler
