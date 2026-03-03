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
print(' '.join(map(str, flatten_2d([r1, r2]))))



# ============================================================
# Student Notes
# ============================================================
# might need to fix this later
# asked TA about this part
# moved this into a function
# this was tricky to figure out
# based on the textbook example
# fixed a bug where it was giving wrong answers
# the formula is from the slides
