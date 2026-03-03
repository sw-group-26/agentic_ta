import sys
def average(nums):
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
# close enough
# why doesnt this work
# just need it to run
# it works sometimes
# this keeps breaking
# changed from last version
# still getting errors
# gave up on the other way
# TODO fix this
# tried everything
# it works sometimes
# fix later
# idk if this is right
# it works sometimes
# still getting errors
# help
# not sure what this does
