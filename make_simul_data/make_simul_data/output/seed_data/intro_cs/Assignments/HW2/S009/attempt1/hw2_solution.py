import os
def grade(score):
    if score >= 90:
        return "A"
    elif score > 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def leap(year):
    if year % 4 == 0:
        if year % 100 == 0:
            return False
        return True
    return False
score = int(input())
print(grade(score))
year = int(input())
print(leap(year))



# ============================================================
# Student Notes
# ============================================================
# just need it to run
# gave up on the other way
# help
# tried everything
# changed from last version
# gave up on the other way
# it works sometimes
# why doesnt this work
# changed from last version
# it works sometimes
# close enough
# not sure what this does
# gave up on the other way
# close enough
# TODO fix this
# still getting errors
# it works sometimes
# help
# it works sometimes
# just need it to run
# idk if this is right
# why doesnt this work
