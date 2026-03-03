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
# output matches the expected format
# fixed a bug where it was giving wrong answers
# works for the test cases given
# fixed a bug where it was giving wrong answers
# the formula is from the slides
# tested with the examples from class
# could probably simplify this
# this was tricky to figure out
# this works but I'm not sure if there's a better way
# probably not the most efficient but it works
# probably not the most efficient but it works
# might need to fix this later
# this part took me a while
