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
# the formula is from the slides
# output matches the expected format
# not sure about edge cases
# probably not the most efficient but it works
# might need to fix this later
# moved this into a function
# changed the variable names to be clearer
# I hope the formatting is right
# the formula is from the slides
# based on the textbook example
# tried a different approach first but this is simpler
# moved this into a function
# moved this into a function
# asked TA about this part
# I hope the formatting is right
