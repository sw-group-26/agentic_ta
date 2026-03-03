"""HW5 Solution: Lists and Data Structures.

Uses manually implemented list utilities from hw5_utils.
"""

from hw5_utils import (
    bubble_sort,
    calc_average,
    count_element,
    flatten_lists,
    get_second_largest,
    make_squares,
    merge_lists,
    unique_elements,
)


def main() -> None:
    """Run all list problems."""
    # Average
    print(calc_average(list(map(int, input().split()))))

    # Remove duplicates
    print(" ".join(map(str, unique_elements(list(map(int, input().split()))))))

    # Sort
    print(" ".join(map(str, bubble_sort(list(map(int, input().split()))))))
    # Second largest
    print(get_second_largest(list(map(int, input().split()))))

    # Count occurrences
    target: int = int(input())
    print(count_element(target, list(map(int, input().split()))))

    # Merge sorted
    a: list[int] = list(map(int, input().split()))
    b: list[int] = list(map(int, input().split()))
    print(" ".join(map(str, merge_lists(a, b))))

    # Squares
    print(" ".join(map(str, make_squares(int(input())))))
    # Flatten
    r1: list[int] = list(map(int, input().split()))
    r2: list[int] = list(map(int, input().split()))
    print(" ".join(map(str, flatten_lists([r1, r2]))))

if __name__ == "__main__":
    main()