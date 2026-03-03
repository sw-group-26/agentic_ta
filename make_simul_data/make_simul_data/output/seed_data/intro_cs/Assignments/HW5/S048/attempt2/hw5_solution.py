"""HW5 Solution: Lists and Data Structures.

Main driver that reads input and calls list utility functions
defined in hw5_utils.py.
"""
from hw5_utils import (
    compute_average,
    count_occurrences,
    flatten,
    generate_squares,
    merge_sorted,
    remove_duplicates,
    second_largest,
    sort_list,
)


def main() -> None:
    """Execute all list problems."""
    # Problem 1: Average
    nums: list[int] = list(map(int, input().split()))
    print(compute_average(nums))

    # Problem 2: Remove duplicates
    nums = list(map(int, input().split()))
    result: list[int] = remove_duplicates(nums)
    print(" ".join(map(str, result)))

    # Problem 3: Sort
    nums = list(map(int, input().split()))
    result = sort_list(nums)
    print(" ".join(map(str, result)))
    # Problem 4: Second largest
    nums = list(map(int, input().split()))
    print(second_largest(nums))

    # Problem 5: Count occurrences
    target: int = int(input())
    nums = list(map(int, input().split()))
    print(count_occurrences(target, nums))

    # Problem 6: Merge sorted lists
    list1: list[int] = list(map(int, input().split()))
    list2: list[int] = list(map(int, input().split()))
    result = merge_sorted(list1, list2)
    print(" ".join(map(str, result)))

    # Problem 7: Squares
    n: int = int(input())
    result = generate_squares(n)
    print(" ".join(map(str, result)))

    # Problem 8: Flatten
    row1: list[int] = list(map(int, input().split()))
    row2: list[int] = list(map(int, input().split()))
    result = flatten([row1, row2])
    print(" ".join(map(str, result)))

if __name__ == "__main__":
    main()