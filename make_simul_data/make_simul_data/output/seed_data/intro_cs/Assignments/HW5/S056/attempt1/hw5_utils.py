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
# just need it to run
# why doesnt this work
# this keeps breaking
# close enough
# tried everything
# tried everything
# gave up on the other way
# it works sometimes
# almost works i think
# it works sometimes
# this keeps breaking
# tried everything
# TODO fix this
# help
# this keeps breaking
# not sure what this does
# close enough
# TODO fix this
# still getting errors
