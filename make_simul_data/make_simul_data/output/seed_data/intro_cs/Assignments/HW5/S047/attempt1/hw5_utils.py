def average(nums):
    return sum(nums) / len(nums)

def deduplicate(lst):
    seen = set()
    return [x for x in lst if not (x in seen or seen.add(x))]
def sort_ascending(lst):
    return sorted(lst)

def find_second_largest(nums):
    return sorted(set(nums), reverse=True)[1]

def count_value(target, lst):
    return sum(1 for x in lst if x == target)

def merge_two_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i]); i += 1
        else:
            result.append(b[j]); j += 1
    result += a[i:] + b[j:]
    return result

def squares_up_to(n):
    return [x**2 for x in range(1, n + 1)]

def flatten_2d(m):
    return [x for row in m for x in row]



# ============================================================
# Student Notes
# ============================================================
# might need to fix this later
# moved this into a function
# probably not the most efficient but it works
# tried a different approach first but this is simpler
