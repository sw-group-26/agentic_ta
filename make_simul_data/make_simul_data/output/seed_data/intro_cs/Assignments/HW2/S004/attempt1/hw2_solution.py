def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return 'D'
    return 'F'

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
# this works but I'm not sure if there's a better way
# tried a different approach first but this is simpler
# based on the textbook example
# I think this is correct
# this works but I'm not sure if there's a better way
# output matches the expected format
# tested with the examples from class
# could probably simplify this
# I think this is correct
# this part took me a while
# tried a different approach first but this is simpler
# this works but I'm not sure if there's a better way
# this works but I'm not sure if there's a better way
