"""HW5 Utility Functions: List manipulation helpers.

Provides functions for computing averages, removing duplicates,
sorting, finding elements, counting, merging, and transforming lists.
"""


def compute_average(numbers: list[int]) -> float:
    """Calculate the arithmetic mean of a list of numbers.
    Args:
        numbers: Non-empty list of integers.

    Returns:
        The average as a float.
    """
    return sum(numbers) / len(numbers)

def remove_duplicates(items: list[int]) -> list[int]:
    """Remove duplicate elements while preserving order.

    Uses a seen-set to track encountered values and builds
    a new list containing only the first occurrence of each value.

    Args:
        items: List that may contain duplicates.
    Returns:
        New list with duplicates removed, original order preserved.
    """
    seen: set[int] = set()
    result: list[int] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def sort_list(items: list[int]) -> list[int]:
    """Sort a list of integers in ascending order.

    Returns a new sorted list without modifying the original.

    Args:
        items: List of integers.
    Returns:
        New list sorted in ascending order.
    """
    return sorted(items)


def second_largest(numbers: list[int]) -> int:
    """Find the second largest unique value in a list.

    Args:
        numbers: List with at least 2 distinct values.

    Returns:
        The second largest value.
    """
    unique: list[int] = sorted(set(numbers), reverse=True)
    return unique[1]

def count_occurrences(target: int, items: list[int]) -> int:
    """Count how many times target appears in items.

    Args:
        target: The value to count.
        items: List to search in.

    Returns:
        Number of occurrences of target.
    """
    count: int = 0
    for item in items:
        if item == target:
            count += 1
    return count


def merge_sorted(list1: list[int], list2: list[int]) -> list[int]:
    """Merge two sorted lists into one sorted list.

    Uses a two-pointer technique for O(n+m) efficiency.

    Args:
        list1: First sorted list.
        list2: Second sorted list.
    Returns:
        Merged sorted list.
    """
    result: list[int] = []
    i: int = 0
    j: int = 0
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result


def generate_squares(n: int) -> list[int]:
    """Generate a list of perfect squares from 1 to n.

    Args:
        n: Upper bound (generate squares of 1, 2, ..., n).

    Returns:
        List of n perfect squares.
    """
    return [i * i for i in range(1, n + 1)]

def flatten(nested: list[list[int]]) -> list[int]:
    """Flatten a 2D list into a 1D list.

    Args:
        nested: List of lists of integers.

    Returns:
        Flattened list with all elements in order.
    """
    result: list[int] = []
    for sublist in nested:
        result.extend(sublist)
    return result