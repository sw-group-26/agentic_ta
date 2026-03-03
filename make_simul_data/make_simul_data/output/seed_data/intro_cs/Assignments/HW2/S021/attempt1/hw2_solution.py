def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    elif s >= 60:
        return 'D'
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
# I hope the formatting is right
# moved this into a function
# asked TA about this part
# not sure about edge cases
# asked TA about this part
# I hope the formatting is right
# this was tricky to figure out
# this part took me a while
# this was tricky to figure out
# I hope the formatting is right
# tested with the examples from class
# I hope the formatting is right
# this was tricky to figure out
# might need to fix this later
# tested with the examples from class
# I hope the formatting is right
# this works but I'm not sure if there's a better way
