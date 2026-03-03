from hw5_utils import *
import sys
print(calc_average(list(map(int, input().split()))))
print(" ".join(map(str, unique_elements(list(map(int, input().split()))))))
print(" ".join(map(str, bubble_sort(list(map(int, input().split()))))))
print(get_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_element(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_lists(a, b))))
print(" ".join(map(str, make_squares(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_lists([r1, r2]))))


# ============================================================
# Student Notes
# ============================================================
# why doesnt this work
# this keeps breaking
# it works sometimes
# close enough
# help
# almost works i think
# this keeps breaking
# help
# idk if this is right
# this keeps breaking
# fix later
# close enough
# why doesnt this work
