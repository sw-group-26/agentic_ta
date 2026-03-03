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
# based on the textbook example
# moved this into a function
# could probably simplify this
# changed the variable names to be clearer
# I hope the formatting is right
# not sure about edge cases
# tried a different approach first but this is simpler
# this was tricky to figure out
# changed the variable names to be clearer
# based on the textbook example
# could probably simplify this
# output matches the expected format
# I think this is correct
# this part took me a while
# I had to look up how input() works
