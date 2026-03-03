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
    # Bug: missing the 400 rule
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
# this keeps breaking
# help
# this keeps breaking
# why doesnt this work
# help
# still getting errors
# idk if this is right
# fix later
# tried everything
# why doesnt this work
# changed from last version
# why doesnt this work
# gave up on the other way
# gave up on the other way
# TODO fix this
# changed from last version
# this keeps breaking
# almost works i think
# almost works i think
# tried everything
# not sure what this does
