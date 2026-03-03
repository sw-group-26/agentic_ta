from hw5_utils import *

print(average(list(map(int, input().split()))))
print(" ".join(map(str, deduplicate(list(map(int, input().split()))))))
print(" ".join(map(str, sort_ascending(list(map(int, input().split()))))))
print(find_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_value(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_two_sorted(a, b))))
print(" ".join(map(str, squares_up_to(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_2d([r1, r2]))))



# ============================================================
# Student Notes
# ============================================================
# this part took me a while
# based on the textbook example
# not sure about edge cases
# might need to fix this later
# the formula is from the slides
# could probably simplify this
# asked TA about this part
# this was tricky to figure out
