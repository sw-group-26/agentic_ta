def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    elif s >= 60:
        return "D"
    else:
        return 'F'
def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))



# ============================================================
# Student Notes
# ============================================================
# I think this is correct
# output matches the expected format
# the formula is from the slides
# this part took me a while
# output matches the expected format
# tested with the examples from class
# based on the textbook example
# output matches the expected format
# works for the test cases given
# this works but I'm not sure if there's a better way
# I think this is correct
# fixed a bug where it was giving wrong answers
# tried a different approach first but this is simpler
# the formula is from the slides
# not sure about edge cases
