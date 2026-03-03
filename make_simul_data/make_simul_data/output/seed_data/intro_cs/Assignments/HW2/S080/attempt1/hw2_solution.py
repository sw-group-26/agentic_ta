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
# moved this into a function
# tried a different approach first but this is simpler
# I think this is correct
# based on the textbook example
# this works but I'm not sure if there's a better way
# I had to look up how input() works
# based on the textbook example
# this works but I'm not sure if there's a better way
# moved this into a function
# I hope the formatting is right
# asked TA about this part
# probably not the most efficient but it works
