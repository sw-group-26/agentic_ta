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
# the formula is from the slides
# moved this into a function
# this part took me a while
# this part took me a while
# probably not the most efficient but it works
# tried a different approach first but this is simpler
# output matches the expected format
# based on the textbook example
# based on the textbook example
# this was tricky to figure out
# this works but I'm not sure if there's a better way
# tried a different approach first but this is simpler
# based on the textbook example
# this works but I'm not sure if there's a better way
