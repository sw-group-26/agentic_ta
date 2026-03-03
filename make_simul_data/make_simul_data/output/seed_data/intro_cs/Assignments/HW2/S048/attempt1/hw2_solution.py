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
# based on the textbook example
# this was tricky to figure out
# I had to look up how input() works
# tested with the examples from class
# I hope the formatting is right
# asked TA about this part
# output matches the expected format
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# moved this into a function
# this was tricky to figure out
