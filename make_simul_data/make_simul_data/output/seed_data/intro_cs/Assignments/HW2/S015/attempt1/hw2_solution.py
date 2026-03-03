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
# I had to look up how input() works
# moved this into a function
# moved this into a function
# output matches the expected format
# asked TA about this part
# this part took me a while
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# this was tricky to figure out
# tested with the examples from class
# I think this is correct
# asked TA about this part
# the formula is from the slides
# this part took me a while
# fixed a bug where it was giving wrong answers
