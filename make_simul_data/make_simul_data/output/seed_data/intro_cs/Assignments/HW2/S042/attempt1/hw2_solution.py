def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return 'B'
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
# this was tricky to figure out
# works for the test cases given
# asked TA about this part
# I think this is correct
# might need to fix this later
# probably not the most efficient but it works
# asked TA about this part
# the formula is from the slides
# not sure about edge cases
# I hope the formatting is right
# probably not the most efficient but it works
# I had to look up how input() works
# I had to look up how input() works
# tried a different approach first but this is simpler
# works for the test cases given
