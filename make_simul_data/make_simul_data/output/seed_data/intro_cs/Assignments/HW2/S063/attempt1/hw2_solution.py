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
# tried a different approach first but this is simpler
# based on the textbook example
# probably not the most efficient but it works
# moved this into a function
# I think this is correct
# tried a different approach first but this is simpler
# I had to look up how input() works
# could probably simplify this
# the formula is from the slides
# this works but I'm not sure if there's a better way
# I think this is correct
# I had to look up how input() works
# I hope the formatting is right
# might need to fix this later
# could probably simplify this
