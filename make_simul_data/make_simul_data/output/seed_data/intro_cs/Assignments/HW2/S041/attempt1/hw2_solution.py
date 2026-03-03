import time
def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    # Bug: missing D grade, jumps to F
    else:
        return "F"

def is_leap(y):
    # Bug: wrong logic - OR instead of AND
    return y % 4 == 0 or y % 100 != 0

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))


# ============================================================
# Student Notes
# ============================================================
# changed from last version
# TODO fix this
# almost works i think
# changed from last version
# why doesnt this work
# it works sometimes
# almost works i think
# still getting errors
# still getting errors
# help
# changed from last version
# TODO fix this
# it works sometimes
# still getting errors
# not sure what this does
# gave up on the other way
# tried everything
# TODO fix this
# tried everything
# almost works i think
# why doesnt this work
# idk if this is right
# fix later
# fix later
