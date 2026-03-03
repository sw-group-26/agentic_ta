"""HW5 Utilities: Manual list implementations.

All list operations implemented manually without relying on
built-in functions like sorted(), set(), or list.count().
"""


def calc_average(numbers: list[int]) -> float:
    """Compute average by summing and dividing manually.
    Args:
        numbers: Non-empty list of integers.

    Returns:
        The arithmetic mean.
    """
    total: int = 0
    for num in numbers:
        total += num
    return total / len(numbers)


def unique_elements(items: list[int]) -> list[int]:
    """Remove duplicates preserving first occurrence order.

    Args:
        items: List with possible duplicates.

    Returns:
        Deduplicated list.
    """
    seen: set[int] = set()
    result: list[int] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def bubble_sort(items: list[int]) -> list[int]:
    """Sort a list using bubble sort algorithm.

    Args:
        items: List of integers.

    Returns:
        New sorted list.
    """
    arr: list[int] = items.copy()
    n: int = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def get_second_largest(numbers: list[int]) -> int:
    """Find second largest by tracking top two values.

    Args:
        numbers: List with at least 2 distinct values.
    Returns:
        The second largest value.
    """
    first: int = max(numbers)
    second: int = min(numbers)
    for num in numbers:
        if num != first and num > second:
            second = num
    return second


def count_element(target: int, items: list[int]) -> int:
    """Count occurrences of target manually.

    Args:
        target: Value to count.
        items: List to search.

    Returns:
        Number of matches.
    """
    count: int = 0
    for item in items:
        if item == target:
            count += 1
    return count
def merge_lists(a: list[int], b: list[int]) -> list[int]:
    """Merge two sorted lists with two-pointer technique.

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
    while i < len(a):
        merged.append(a[i])
        i += 1
    while j < len(b):
        merged.append(b[j])
        j += 1
    return merged


def make_squares(n: int) -> list[int]:
    """Create list of squares from 1 to n.
    Args:
        n: Upper bound.
    Returns:
        List [1, 4, 9, ..., n*n].
    """
    squares: list[int] = []
    for i in range(1, n + 1):
        squares.append(i * i)
    return squares
def flatten_lists(nested: list[list[int]]) -> list[int]:
    """Flatten a list of lists into a single list.

    Args:
        nested: 2D list.

    Returns:
        Flattened 1D list.
    """
    flat: list[int] = []
    for sublist in nested:
        for item in sublist:
            flat.append(item)
    return flat
