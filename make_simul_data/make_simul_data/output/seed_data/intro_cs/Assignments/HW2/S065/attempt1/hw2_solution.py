def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"
def is_leap(year):
    if year % 400 == 0: return True
    if year % 100 == 0: return False
    return year % 4 == 0
score = int(input())
print(assign_grade(score))
year = int(input())
print(is_leap(year))



# ============================================================
# Student Notes
# ============================================================
# not sure about edge cases
# this was tricky to figure out
# the formula is from the slides
# output matches the expected format
# output matches the expected format
# I think this is correct
# changed the variable names to be clearer
# tested with the examples from class
# tested with the examples from class
# this works but I'm not sure if there's a better way
# asked TA about this part
# output matches the expected format
# fixed a bug where it was giving wrong answers
# output matches the expected format
