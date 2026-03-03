def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return 'B'
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
# I had to look up how input() works
# output matches the expected format
# asked TA about this part
# based on the textbook example
# tested with the examples from class
# changed the variable names to be clearer
# could probably simplify this
# tested with the examples from class
# tried a different approach first but this is simpler
# might need to fix this later
# might need to fix this later
# tested with the examples from class
# works for the test cases given
# this works but I'm not sure if there's a better way
# I had to look up how input() works
