from hw5_utils import *

print(calc_average(list(map(int, input().split()))))
print(" ".join(map(str, unique_elements(list(map(int, input().split()))))))
print(' '.join(map(str, bubble_sort(list(map(int, input().split()))))))
print(get_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_element(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_lists(a, b))))
print(" ".join(map(str, make_squares(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(' '.join(map(str, flatten_lists([r1, r2]))))



# ============================================================
# Student Notes
# ============================================================
# probably not the most efficient but it works
# might need to fix this later
# the formula is from the slides
# I hope the formatting is right
# moved this into a function
# tested with the examples from class
# tested with the examples from class
