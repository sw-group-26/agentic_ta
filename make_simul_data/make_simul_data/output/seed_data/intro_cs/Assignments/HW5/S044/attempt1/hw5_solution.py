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
# could probably simplify this
# this was tricky to figure out
# I hope the formatting is right
# tested with the examples from class
# tried a different approach first but this is simpler
# this was tricky to figure out
# the formula is from the slides
