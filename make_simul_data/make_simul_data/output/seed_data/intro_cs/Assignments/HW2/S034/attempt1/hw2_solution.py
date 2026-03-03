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
        return "F"

def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))



# ============================================================
# Student Notes
# ============================================================
# tested with the examples from class
# based on the textbook example
# this part took me a while
# this part took me a while
# output matches the expected format
# could probably simplify this
# might need to fix this later
# fixed a bug where it was giving wrong answers
# changed the variable names to be clearer
# fixed a bug where it was giving wrong answers
# not sure about edge cases
# this was tricky to figure out
# output matches the expected format
# output matches the expected format
# probably not the most efficient but it works
