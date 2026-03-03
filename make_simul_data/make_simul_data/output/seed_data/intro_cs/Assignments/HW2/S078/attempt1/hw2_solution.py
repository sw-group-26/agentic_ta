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
# could probably simplify this
# probably not the most efficient but it works
# based on the textbook example
# might need to fix this later
# I think this is correct
# might need to fix this later
# I had to look up how input() works
# fixed a bug where it was giving wrong answers
# this was tricky to figure out
# this works but I'm not sure if there's a better way
# could probably simplify this
# I think this is correct
# not sure about edge cases
# I had to look up how input() works
# this works but I'm not sure if there's a better way
