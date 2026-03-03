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
# tested with the examples from class
# not sure about edge cases
# output matches the expected format
# tried a different approach first but this is simpler
# I think this is correct
# tested with the examples from class
# might need to fix this later
# might need to fix this later
# tested with the examples from class
# output matches the expected format
# not sure about edge cases
# could probably simplify this
# this part took me a while
