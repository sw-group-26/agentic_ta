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
# works for the test cases given
# might need to fix this later
# tried a different approach first but this is simpler
# I think this is correct
# asked TA about this part
# might need to fix this later
# moved this into a function
# not sure about edge cases
# output matches the expected format
# I hope the formatting is right
# this was tricky to figure out
# this was tricky to figure out
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# could probably simplify this
