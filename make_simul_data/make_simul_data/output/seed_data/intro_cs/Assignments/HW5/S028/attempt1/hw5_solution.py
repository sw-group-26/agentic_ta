from hw5_utils import *

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
# this part took me a while
# I hope the formatting is right
# based on the textbook example
# this was tricky to figure out
# I hope the formatting is right
# this part took me a while
# I had to look up how input() works
# this was tricky to figure out
