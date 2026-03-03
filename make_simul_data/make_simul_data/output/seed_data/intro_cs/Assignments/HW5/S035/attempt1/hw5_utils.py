import sys
def calc_average(nums):
    # Bug: integer division
    total = 0
    for n in nums: total += n
    return total // len(nums)

def unique_elements(lst):
    return list(set(lst))

def bubble_sort(lst):
    arr = lst.copy()
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def get_second_largest(nums):
    nums_s = sorted(nums, reverse=True)
    return nums_s[1]

def count_element(target, lst):
    c = 0
    for x in lst:
        if x == target: c += 1
    return c
def merge_lists(a, b):
    return sorted(a + b)

def make_squares(n):
    return [i*i for i in range(1, n+1)]

def flatten_lists(nested):
    res = []
    for sub in nested:
        for x in sub: res.append(x)
    return res



# ============================================================
# Student Notes
# ============================================================
# changed from last version
# almost works i think
