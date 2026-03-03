import time
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
# idk if this is right
# changed from last version
# still getting errors
# gave up on the other way
# idk if this is right
# almost works i think
# just need it to run
# TODO fix this
# why doesnt this work
# close enough
# help
# it works sometimes
# fix later
# just need it to run
# just need it to run
