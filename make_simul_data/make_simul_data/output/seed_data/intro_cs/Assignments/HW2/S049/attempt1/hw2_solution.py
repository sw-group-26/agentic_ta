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
# this was tricky to figure out
# based on the textbook example
# probably not the most efficient but it works
# output matches the expected format
# works for the test cases given
# output matches the expected format
# this part took me a while
# I had to look up how input() works
# not sure about edge cases
# output matches the expected format
# output matches the expected format
