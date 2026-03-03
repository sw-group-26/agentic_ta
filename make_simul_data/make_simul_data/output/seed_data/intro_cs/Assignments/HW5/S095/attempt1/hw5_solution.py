from hw5_utils import *
print(average(list(map(int, input().split()))))
print(" ".join(map(str, deduplicate(list(map(int, input().split()))))))
print(" ".join(map(str, sort_ascending(list(map(int, input().split()))))))
print(find_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_value(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(' '.join(map(str, merge_two_sorted(a, b))))
print(" ".join(map(str, squares_up_to(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_2d([r1, r2]))))



# ============================================================
# Student Notes
# ============================================================
# asked TA about this part
# this part took me a while
# this part took me a while
# tested with the examples from class
# based on the textbook example
# I think this is correct
# moved this into a function
# changed the variable names to be clearer
