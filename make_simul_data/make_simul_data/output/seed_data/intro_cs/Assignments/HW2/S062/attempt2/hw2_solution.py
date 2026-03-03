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
# output matches the expected format
# tested with the examples from class
# output matches the expected format
# I had to look up how input() works
# could probably simplify this
# based on the textbook example
# might need to fix this later
# the formula is from the slides
# might need to fix this later
# this part took me a while
# asked TA about this part
# might need to fix this later
# this part took me a while
# not sure about edge cases
