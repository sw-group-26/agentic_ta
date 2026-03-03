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
# this was tricky to figure out
# works for the test cases given
# moved this into a function
# based on the textbook example
# tried a different approach first but this is simpler
# could probably simplify this
# I hope the formatting is right
# tried a different approach first but this is simpler
# I had to look up how input() works
# asked TA about this part
# I think this is correct
# could probably simplify this
# I think this is correct
# tested with the examples from class
# the formula is from the slides
