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
# tried a different approach first but this is simpler
# works for the test cases given
# tried a different approach first but this is simpler
# tried a different approach first but this is simpler
# tried a different approach first but this is simpler
# fixed a bug where it was giving wrong answers
# this works but I'm not sure if there's a better way
# this works but I'm not sure if there's a better way
# might need to fix this later
