def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
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
# fixed a bug where it was giving wrong answers
# could probably simplify this
# the formula is from the slides
# might need to fix this later
# not sure about edge cases
# could probably simplify this
# the formula is from the slides
# moved this into a function
# asked TA about this part
# works for the test cases given
# I had to look up how input() works
# this was tricky to figure out
# tested with the examples from class
# works for the test cases given
# asked TA about this part
# not sure about edge cases
