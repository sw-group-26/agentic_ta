def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return 'C'
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
# I hope the formatting is right
# probably not the most efficient but it works
# could probably simplify this
# based on the textbook example
# not sure about edge cases
# moved this into a function
# based on the textbook example
# moved this into a function
# the formula is from the slides
# the formula is from the slides
# moved this into a function
# I had to look up how input() works
# fixed a bug where it was giving wrong answers
# might need to fix this later
# changed the variable names to be clearer
