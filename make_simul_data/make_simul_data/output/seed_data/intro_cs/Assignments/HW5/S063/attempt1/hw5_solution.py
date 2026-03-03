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
# asked TA about this part
# I had to look up how input() works
# tested with the examples from class
# might need to fix this later
# probably not the most efficient but it works
# might need to fix this later
# asked TA about this part
