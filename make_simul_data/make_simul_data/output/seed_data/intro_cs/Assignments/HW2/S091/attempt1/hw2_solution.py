def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
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
# I think this is correct
# this works but I'm not sure if there's a better way
# output matches the expected format
# I had to look up how input() works
# output matches the expected format
# tested with the examples from class
# the formula is from the slides
# fixed a bug where it was giving wrong answers
# asked TA about this part
# not sure about edge cases
# probably not the most efficient but it works
# asked TA about this part
