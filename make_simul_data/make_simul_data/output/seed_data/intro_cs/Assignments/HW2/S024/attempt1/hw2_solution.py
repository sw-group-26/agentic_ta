def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return 'D'
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
# moved this into a function
# I think this is correct
# moved this into a function
# tested with the examples from class
# probably not the most efficient but it works
# this was tricky to figure out
# I had to look up how input() works
# this was tricky to figure out
# based on the textbook example
# based on the textbook example
# might need to fix this later
# output matches the expected format
# tested with the examples from class
# could probably simplify this
# I hope the formatting is right
