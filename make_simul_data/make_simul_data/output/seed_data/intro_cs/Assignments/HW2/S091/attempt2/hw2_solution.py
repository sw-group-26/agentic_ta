def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return 'C'
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
# asked TA about this part
# asked TA about this part
# this works but I'm not sure if there's a better way
# I think this is correct
# this part took me a while
# fixed a bug where it was giving wrong answers
# probably not the most efficient but it works
# might need to fix this later
# probably not the most efficient but it works
# I think this is correct
# I think this is correct
# based on the textbook example
# asked TA about this part
# I had to look up how input() works
# output matches the expected format
# I had to look up how input() works
