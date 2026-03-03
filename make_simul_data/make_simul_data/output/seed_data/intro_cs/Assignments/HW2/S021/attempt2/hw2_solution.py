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
# output matches the expected format
# I had to look up how input() works
# this works but I'm not sure if there's a better way
# could probably simplify this
# probably not the most efficient but it works
# I think this is correct
# I think this is correct
# probably not the most efficient but it works
# might need to fix this later
# this part took me a while
# might need to fix this later
# based on the textbook example
# based on the textbook example
# this was tricky to figure out
# I hope the formatting is right
# this part took me a while
