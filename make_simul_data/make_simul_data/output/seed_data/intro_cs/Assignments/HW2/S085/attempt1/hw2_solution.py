def assign_grade(score):
    if score >= 90: return 'A'
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
# could probably simplify this
# the formula is from the slides
# I hope the formatting is right
# tried a different approach first but this is simpler
# moved this into a function
# tested with the examples from class
# asked TA about this part
# not sure about edge cases
# tested with the examples from class
# I hope the formatting is right
# tried a different approach first but this is simpler
# moved this into a function
# probably not the most efficient but it works
# this part took me a while
