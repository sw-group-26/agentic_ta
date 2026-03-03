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
# this part took me a while
# probably not the most efficient but it works
# tried a different approach first but this is simpler
# output matches the expected format
# I had to look up how input() works
# this part took me a while
# moved this into a function
# I hope the formatting is right
# tried a different approach first but this is simpler
# asked TA about this part
# moved this into a function
# works for the test cases given
# output matches the expected format
# probably not the most efficient but it works
