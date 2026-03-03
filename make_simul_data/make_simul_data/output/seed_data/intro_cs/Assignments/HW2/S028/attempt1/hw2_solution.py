def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
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
# moved this into a function
# this was tricky to figure out
# this part took me a while
# fixed a bug where it was giving wrong answers
# not sure about edge cases
# the formula is from the slides
# moved this into a function
# moved this into a function
# works for the test cases given
# the formula is from the slides
# this was tricky to figure out
# this was tricky to figure out
# probably not the most efficient but it works
