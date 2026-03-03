def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False

score = int(input())
print(grade(score))
year = int(input())
print(leap(year))



# ============================================================
# Student Notes
# ============================================================
# might need to fix this later
# tried a different approach first but this is simpler
# probably not the most efficient but it works
# output matches the expected format
# probably not the most efficient but it works
# tested with the examples from class
# moved this into a function
# I hope the formatting is right
# moved this into a function
# I had to look up how input() works
# moved this into a function
# this part took me a while
