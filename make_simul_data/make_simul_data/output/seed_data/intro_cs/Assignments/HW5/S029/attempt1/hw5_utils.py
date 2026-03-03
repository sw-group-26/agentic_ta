"""HW5 Utilities: List operations using comprehensions and built-ins.
Emphasizes Pythonic idioms like list comprehensions, built-in
functions, and generator expressions where appropriate.
"""
def average(numbers: list[int]) -> float:
    """Compute the mean of a list of numbers.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        The arithmetic mean as a float.
    """
    return sum(numbers) / len(numbers)


def deduplicate(items: list[int]) -> list[int]:
    """Remove duplicates while preserving insertion order.

    Args:
        items: List with possible duplicates.

    Returns:
        Deduplicated list in original order.
    """
    seen: set[int] = set()
    return [x for x in items if not (x in seen or seen.add(x))]

def sort_ascending(items: list[int]) -> list[int]:
    """Return a sorted copy of the list.

    Args:
        items: List of integers.

    Returns:
        Sorted list in ascending order.
    """
    return sorted(items)

def find_second_largest(numbers: list[int]) -> int:
    """Find the second largest unique value.

    Args:
        numbers: List with at least 2 distinct values.

    Returns:
        Second largest unique value.
    """
    unique_sorted: list[int] = sorted(set(numbers), reverse=True)
    return unique_sorted[1]

def count_value(target: int, items: list[int]) -> int:
    """Count occurrences of target in items.

    Args:
        target: Value to count.
        items: List to search.

    Returns:
        Count of target in items.
    """
    return sum(1 for x in items if x == target)


def merge_two_sorted(a: list[int], b: list[int]) -> list[int]:
    """Merge two sorted lists using two-pointer technique.

    Args:
        a: First sorted list.
        b: Second sorted list.
    Returns:
        Merged sorted list.
    """
    merged: list[int] = []
    i: int = 0
    j: int = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            merged.append(a[i])
            i += 1
        else:
            merged.append(b[j])
            j += 1
    merged.extend(a[i:])
    merged.extend(b[j:])
    return merged

def squares_up_to(n: int) -> list[int]:
    """Generate squares of integers from 1 to n.
    Args:
        n: Upper bound.

    Returns:
        List of squares [1, 4, 9, ..., n*n].
    """
    return [x ** 2 for x in range(1, n + 1)]


def flatten_2d(matrix: list[list[int]]) -> list[int]:
    """Flatten a 2D list to 1D using a comprehension.

    Args:
        matrix: List of lists.

    Returns:
        Flattened list.
    """
    return [item for row in matrix for item in row]
