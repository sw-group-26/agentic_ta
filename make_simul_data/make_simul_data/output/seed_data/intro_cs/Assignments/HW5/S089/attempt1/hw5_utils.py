def average(nums):
    return sum(nums) // len(nums)
def deduplicate(lst):
    # Bug: uses set() which doesn't preserve order
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
# fix later
# close enough
# almost works i think
# it works sometimes
# idk if this is right
# TODO fix this
# just need it to run
# changed from last version
# just need it to run
# not sure what this does
# gave up on the other way
# tried everything
# it works sometimes
# fix later
# changed from last version
