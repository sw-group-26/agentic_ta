import sys
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
# changed from last version
# changed from last version
# help
# help
# this keeps breaking
# why doesnt this work
# why doesnt this work
# still getting errors
# just need it to run
# it works sometimes
# tried everything
# it works sometimes
# gave up on the other way
# idk if this is right
# just need it to run
