import os
def average(nums):
    # Bug: integer division
    return sum(nums) // len(nums)

def deduplicate(lst):
    return list(set(lst))

def sort_ascending(lst):
    return sorted(lst)

def find_second_largest(nums):
    s = sorted(nums, reverse=True)
    return s[1]

def count_value(target, lst):
    c = 0
    for x in lst:
        if x == target: c += 1
    return c

def merge_two_sorted(a, b):
    return sorted(a + b)

def squares_up_to(n):
    return [x**2 for x in range(1, n + 1)]

def flatten_2d(m):
    return [x for row in m for x in row]



# ============================================================
# Student Notes
# ============================================================
# TODO fix this
# still getting errors
# help
# just need it to run
# why doesnt this work
# this keeps breaking
# this keeps breaking
# this keeps breaking
# tried everything
# just need it to run
# fix later
# fix later
# this keeps breaking
# gave up on the other way
# almost works i think
# it works sometimes
# this keeps breaking
