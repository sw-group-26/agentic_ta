def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return 'C'
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
# probably not the most efficient but it works
# moved this into a function
# output matches the expected format
# moved this into a function
# tried a different approach first but this is simpler
# output matches the expected format
# asked TA about this part
# changed the variable names to be clearer
# might need to fix this later
# I think this is correct
# tested with the examples from class
# based on the textbook example
