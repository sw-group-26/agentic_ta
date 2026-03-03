def calc_average(nums):
    total = 0
    for n in nums: total += n
    return total / len(nums)
def unique_elements(lst):
    seen = set()
    res = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            res.append(x)
    return res

def bubble_sort(lst):
    arr = lst.copy()
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
def get_second_largest(nums):
    first = max(nums)
    second = min(nums)
    for n in nums:
        if n != first and n > second:
            second = n
    return second

def count_element(target, lst):
    c = 0
    for x in lst:
        if x == target: c += 1
    return c

def merge_lists(a, b):
    res = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]: res.append(a[i]); i += 1
        else: res.append(b[j]); j += 1
    res += a[i:] + b[j:]
    return res

def make_squares(n):
    return [i*i for i in range(1, n+1)]

def flatten_lists(nested):
    res = []
    for sub in nested:
        for x in sub: res.append(x)
    return res