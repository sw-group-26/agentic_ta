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
# changed the variable names to be clearer
# I think this is correct
# tried a different approach first but this is simpler
# moved this into a function
# works for the test cases given
# not sure about edge cases
# moved this into a function
# probably not the most efficient but it works
# might need to fix this later
# might need to fix this later
# not sure about edge cases
# works for the test cases given
# might need to fix this later
# output matches the expected format
# could probably simplify this
