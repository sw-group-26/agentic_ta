import time
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
# gave up on the other way
# close enough
# this keeps breaking
# tried everything
# help
# this keeps breaking
# changed from last version
# changed from last version
# idk if this is right
# it works sometimes
# still getting errors
# gave up on the other way
# fix later
# this keeps breaking
# gave up on the other way
# almost works i think
# help
# changed from last version
# idk if this is right
# why doesnt this work
# idk if this is right
# fix later
