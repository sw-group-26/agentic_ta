from hw5_utils import *

nums = list(map(int, input().split()))
print(compute_average(nums))
nums = list(map(int, input().split()))
print(" ".join(map(str, remove_duplicates(nums))))
nums = list(map(int, input().split()))
print(" ".join(map(str, sort_list(nums))))
nums = list(map(int, input().split()))
print(second_largest(nums))
target = int(input())
nums = list(map(int, input().split()))
print(count_occurrences(target, nums))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_sorted(a, b))))
n = int(input())
print(" ".join(map(str, generate_squares(n))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten([r1, r2]))))


# ============================================================
# Student Notes
# ============================================================
# could probably simplify this
# tested with the examples from class
# I think this is correct
# output matches the expected format
# tested with the examples from class
