def grade(score):
    if score >= 90:
        return 'A'
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
# might need to fix this later
# this was tricky to figure out
# based on the textbook example
# changed the variable names to be clearer
# not sure about edge cases
# this part took me a while
# might need to fix this later
# changed the variable names to be clearer
# this part took me a while
# tried a different approach first but this is simpler
# could probably simplify this
# moved this into a function
