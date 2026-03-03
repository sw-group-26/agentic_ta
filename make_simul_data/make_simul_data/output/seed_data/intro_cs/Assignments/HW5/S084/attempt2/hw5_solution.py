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
print(' '.join(map(str, make_squares(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(' '.join(map(str, flatten_lists([r1, r2]))))


# ============================================================
# Student Notes
# ============================================================
# based on the textbook example
# this works but I'm not sure if there's a better way
# based on the textbook example
# not sure about edge cases
# this works but I'm not sure if there's a better way
# works for the test cases given
