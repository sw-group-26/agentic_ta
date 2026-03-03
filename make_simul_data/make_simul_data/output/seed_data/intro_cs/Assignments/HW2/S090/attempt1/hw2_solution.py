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
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# moved this into a function
# I hope the formatting is right
# I think this is correct
# works for the test cases given
# this was tricky to figure out
# fixed a bug where it was giving wrong answers
# this part took me a while
# based on the textbook example
# not sure about edge cases
# moved this into a function
# works for the test cases given
# tested with the examples from class
# based on the textbook example
