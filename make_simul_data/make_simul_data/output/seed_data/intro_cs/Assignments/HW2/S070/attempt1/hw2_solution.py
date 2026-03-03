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
# it works sometimes
# help
# still getting errors
# still getting errors
# tried everything
# this keeps breaking
# almost works i think
# idk if this is right
# help
# idk if this is right
# just need it to run
# idk if this is right
# why doesnt this work
# gave up on the other way
# this keeps breaking
# almost works i think
# almost works i think
# close enough
# this keeps breaking
# fix later
# this keeps breaking
# TODO fix this
