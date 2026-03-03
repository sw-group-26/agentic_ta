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
# the formula is from the slides
# I think this is correct
# I hope the formatting is right
# could probably simplify this
# this was tricky to figure out
# fixed a bug where it was giving wrong answers
# I hope the formatting is right
# this part took me a while
# tried a different approach first but this is simpler
# this works but I'm not sure if there's a better way
# this works but I'm not sure if there's a better way
# based on the textbook example
# changed the variable names to be clearer
