import os
def compute_average(nums):
    # Bug: integer division
    return sum(nums) // len(nums)

def remove_duplicates(lst):
    return list(set(lst))

def sort_list(lst):
    return sorted(lst)

def second_largest(nums):
    nums_sorted = sorted(nums, reverse=True)
    return nums_sorted[1]
def count_occurrences(target, lst):
    return lst.count(target)
def merge_sorted(a, b):
    return sorted(a + b)
def generate_squares(n):
    return [i**2 for i in range(1, n + 1)]

def flatten(nested):
    result = []
    for sub in nested:
        result.extend(sub)
    return result



# ============================================================
# Student Notes
# ============================================================
# almost works i think
# close enough
# this keeps breaking
# changed from last version
# help
# why doesnt this work
# just need it to run
# almost works i think
# this keeps breaking
# not sure what this does
# it works sometimes
# TODO fix this
# why doesnt this work
# tried everything
# TODO fix this
