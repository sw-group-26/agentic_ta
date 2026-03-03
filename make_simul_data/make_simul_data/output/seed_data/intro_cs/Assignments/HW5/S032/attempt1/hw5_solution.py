"""HW5 Solution: Lists and Data Structures.

Pythonic approach using list comprehension utilities.
"""

from hw5_utils import (
    average,
    count_value,
    deduplicate,
    find_second_largest,
    flatten_2d,
    merge_two_sorted,
    sort_ascending,
    squares_up_to,
)

def main() -> None:
    """Process all list problems."""
    # Average
    print(average(list(map(int, input().split()))))

    # Remove duplicates
    print(" ".join(map(str, deduplicate(list(map(int, input().split()))))))

    # Sort
    print(" ".join(map(str, sort_ascending(list(map(int, input().split()))))))

    # Second largest
    print(find_second_largest(list(map(int, input().split()))))

    # Count occurrences
    target: int = int(input())
    print(count_value(target, list(map(int, input().split()))))

    # Merge sorted
    a: list[int] = list(map(int, input().split()))
    b: list[int] = list(map(int, input().split()))
    print(" ".join(map(str, merge_two_sorted(a, b))))

    # Squares
    print(" ".join(map(str, squares_up_to(int(input())))))
    # Flatten
    r1: list[int] = list(map(int, input().split()))
    r2: list[int] = list(map(int, input().split()))
    print(" ".join(map(str, flatten_2d([r1, r2]))))

if __name__ == "__main__":
    main()
