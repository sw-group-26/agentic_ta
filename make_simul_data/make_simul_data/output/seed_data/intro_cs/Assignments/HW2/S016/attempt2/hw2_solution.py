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
# the formula is from the slides
# I hope the formatting is right
# fixed a bug where it was giving wrong answers
# fixed a bug where it was giving wrong answers
# not sure about edge cases
# not sure about edge cases
# the formula is from the slides
# this part took me a while
# this was tricky to figure out
# this part took me a while
# this part took me a while
# I hope the formatting is right
# this was tricky to figure out
# I had to look up how input() works
# based on the textbook example
# this was tricky to figure out
