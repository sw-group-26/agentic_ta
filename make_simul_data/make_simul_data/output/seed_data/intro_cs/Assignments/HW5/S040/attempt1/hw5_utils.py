def compute_average(nums):
    # Bug: integer division
    return sum(nums) // len(nums)

def remove_duplicates(lst):
    # Bug: set() doesn't preserve order
    return list(set(lst))

def sort_list(lst):
    return sorted(lst)

def second_largest(nums):
    # Bug: doesn't handle duplicates properly
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
# TODO fix this
# changed from last version
# why doesnt this work
# tried everything
# gave up on the other way
# just need it to run
# gave up on the other way
# TODO fix this
# almost works i think
# close enough
# almost works i think
