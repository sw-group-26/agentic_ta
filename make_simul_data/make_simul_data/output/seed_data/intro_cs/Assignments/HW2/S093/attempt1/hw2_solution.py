def assign_grade(score):
    # Bug: wrong boundary - uses > instead of >=
    if score > 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"

def is_leap(year):
    if year % 4 == 0:
        return True
    return False
score = int(input())
print(assign_grade(score))
year = int(input())
print(is_leap(year))


# ============================================================
# Student Notes
# ============================================================
# changed from last version
# almost works i think
# help
# why doesnt this work
# still getting errors
# fix later
# almost works i think
# it works sometimes
# gave up on the other way
# idk if this is right
# changed from last version
# this keeps breaking
# just need it to run
# fix later
# close enough
# fix later
# help
# just need it to run
# this keeps breaking
# changed from last version
# help
# almost works i think
# fix later
# help
# close enough
# why doesnt this work
# changed from last version
