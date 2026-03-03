def compute_average(nums):
    return sum(nums) / len(nums)

def remove_duplicates(lst):
    seen = set()
    result = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

def sort_list(lst):
    return sorted(lst)

def second_largest(nums):
    unique = sorted(set(nums), reverse=True)
    return unique[1]

def count_occurrences(target, lst):
    return lst.count(target)

def merge_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result += a[i:]
    result += b[j:]
    return result

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
# fixed a bug where it was giving wrong answers
