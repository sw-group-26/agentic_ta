"""Assignment definitions and test case specifications for the seed data pipeline.

This module defines the 5 CS1 homework assignments and their associated
test cases. Each assignment is represented as an AssignmentDef (frozen
dataclass from config.py), and each test case as a TestCaseSpec (frozen
dataclass defined here).

The assignments progress in difficulty from basic I/O (HW1) to list
manipulation (HW5), mirroring a typical CS1 semester curriculum at
Georgia State University.

Key exports:
    ASSIGNMENTS         -- Tuple of 5 AssignmentDef instances.
    DIFFICULTY_WEIGHTS   -- Maps integer difficulty (1-5) to float weight.
    get_test_cases()     -- Retrieve TestCaseSpec tuples per assignment.
    get_assignment_by_id() -- Look up a single AssignmentDef by ID.

Module dependency graph:
    config.py  -->  assignments.py  (imports AssignmentDef, NUM_ASSIGNMENTS,
                                     SEMESTER_START, SEMESTER_END)

Consumed by:
    generate_data.py    (iterates over ASSIGNMENTS in the main loop)
    code_generator.py   (uses assignment metadata for code generation)
    grading_engine.py   (uses test cases and difficulty for scoring)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from make_simul_data.seed_data.config import (
    NUM_ASSIGNMENTS,
    SEMESTER_END,
    SEMESTER_START,
    AssignmentDef,
)

# ── Data Structures ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class TestCaseSpec:
    """Immutable definition of a single test case for an assignment.

    Each test case defines an input-output pair that student code is
    evaluated against. In the seed data pipeline, test cases are not
    actually executed; they are used by grading_engine.py to simulate
    pass/fail outcomes and by code_generator.py as reference for
    generating realistic student code.

    The test_case_id format is "{assignment_id}_TC{number:02d}"
    (e.g., "HW1_TC01", "HW3_TC07"). This format matches the
    test_case_id field in the TestCaseResult Pydantic model (models.py).

    Created by: _build_test_cases() in this module (called at import time).
    Used by: grading_engine.py (determines number of test cases and
             points per test case for scoring simulation),
             code_generator.py (generates code targeting these inputs)

    Attributes:
        test_case_id:    Unique identifier string in "{HW_ID}_TC{NN}"
                         format (e.g., "HW1_TC01"). Matches the
                         TestCaseResult.test_case_id field in models.py.
        description:     Brief human-readable description of what the test
                         case checks (e.g., "Convert 0 Celsius to 32 F").
                         Used for logging and debugging purposes.
        input_data:      Input string to be passed to the student's program
                         via stdin or function arguments. May be multi-line
                         for programs that read multiple inputs. Lines are
                         separated by newline characters.
        expected_output: Expected output string from correct student code.
                         Used by grading_engine.py to simulate output
                         matching. Contains trailing newlines matching
                         typical print() output.
        points:          Point value awarded when this test case passes.
                         The sum of all test case points for an assignment
                         equals that assignment's max_score (100). Points
                         are distributed using integer division with
                         remainder going to the first test cases.
    """

    test_case_id: str
    description: str
    input_data: str
    expected_output: str
    points: float


# ── Constants ───────────────────────────────────────────────────────────

# Mapping from integer difficulty level (1-5) to float difficulty weight
# (0.0-1.0). The weight is used by grading_engine.py to adjust score
# distributions via the formula:
#     effective_score = raw_score * (1 - difficulty_weight * 0.3)
# Higher weights result in lower average scores for harder assignments.
#
# Mapping rationale:
#     1 (easiest) -> 0.20  (HW1: Variables, I/O — minimal challenge)
#     2           -> 0.35  (HW2: Conditionals — moderate logic)
#     3           -> 0.50  (HW3: Loops — iteration complexity)
#     4           -> 0.65  (HW4: Functions — abstraction skills)
#     5 (hardest) -> 0.80  (HW5: Lists — data structure manipulation)
#
# Used by: grading_engine.py (to scale scores based on assignment difficulty)
DIFFICULTY_WEIGHTS: dict[int, float] = {
    1: 0.20,
    2: 0.35,
    3: 0.50,
    4: 0.65,
    5: 0.80,
}


# ── Private Helper Functions ────────────────────────────────────────────


def _compute_due_dates(num_assignments: int = NUM_ASSIGNMENTS) -> list[str]:
    """Compute evenly spaced due dates across the semester for all assignments.

    Due dates are distributed uniformly between SEMESTER_START and
    SEMESTER_END, ensuring roughly equal spacing between assignments.
    The first assignment is due ~2-3 weeks after semester start, and
    the last is due ~1 week before semester end.

    Algorithm:
        1. Parse SEMESTER_START and SEMESTER_END as date objects.
        2. Compute total semester duration in days.
        3. Divide the semester into (num_assignments + 1) equal segments.
        4. Place each due date at the boundary of each segment.

    Note: Due dates may fall on weekends. For seed data purposes this is
    acceptable — due dates are used only for timestamp generation, not
    for academic scheduling.

    Used by: _build_assignments() (to assign due dates to AssignmentDef)

    Args:
        num_assignments: Number of due dates to generate.
                         Default: NUM_ASSIGNMENTS (5).

    Returns:
        A list of ISO 8601 date strings (e.g., ["2026-02-01", ...]).
        The list length equals num_assignments, in chronological order.
    """
    start: date = date.fromisoformat(SEMESTER_START)
    end: date = date.fromisoformat(SEMESTER_END)
    total_days: int = (end - start).days

    # Divide the semester into (num_assignments + 1) equal intervals.
    # Each assignment's due date is placed at interval * i from start.
    interval: int = total_days // (num_assignments + 1)

    due_dates: list[str] = []
    for i in range(1, num_assignments + 1):
        due: date = start + timedelta(days=interval * i)
        due_dates.append(due.isoformat())

    return due_dates


def _distribute_points(max_score: int, num_test_cases: int) -> list[float]:
    """Distribute max_score evenly across test cases with integer precision.

    Uses integer division to split points, distributing the remainder
    to the first test cases so the total always sums exactly to max_score.

    Example for max_score=100, num_test_cases=6:
        base = 100 // 6 = 16, remainder = 100 % 6 = 4
        Points: [17, 17, 17, 17, 16, 16]  (sum = 100)

    Example for max_score=100, num_test_cases=8:
        base = 100 // 8 = 12, remainder = 100 % 8 = 4
        Points: [13, 13, 13, 13, 12, 12, 12, 12]  (sum = 100)

    Used by: _build_test_cases() (to assign point values to each TestCaseSpec)

    Args:
        max_score: Total points to distribute (e.g., 100).
        num_test_cases: Number of test cases to distribute across.

    Returns:
        A list of float point values with length num_test_cases.
        The sum of all values equals max_score exactly.
    """
    base: int = max_score // num_test_cases
    remainder: int = max_score % num_test_cases

    # First 'remainder' test cases get (base + 1) points,
    # remaining test cases get 'base' points.
    points: list[float] = []
    for i in range(num_test_cases):
        if i < remainder:
            points.append(float(base + 1))
        else:
            points.append(float(base))

    return points


def _build_assignments() -> tuple[AssignmentDef, ...]:
    """Build the immutable tuple of 5 CS1 homework assignment definitions.

    Creates AssignmentDef instances for each homework assignment in the
    CS1 curriculum, with evenly-spaced due dates across the semester.
    This function is called once at module load time to populate the
    ASSIGNMENTS module-level constant.

    The 5 assignments follow a standard CS1 progression:
        HW1: Variables, I/O, Arithmetic  (difficulty=1, 5 test cases)
        HW2: Conditionals, Boolean Logic (difficulty=2, 6 test cases)
        HW3: Loops and Iteration         (difficulty=3, 7 test cases)
        HW4: Functions, Modular Design   (difficulty=4, 8 test cases)
        HW5: Lists, Data Structures      (difficulty=5, 8 test cases)

    Used by: module-level ASSIGNMENTS constant initialization.

    Returns:
        A tuple of 5 AssignmentDef instances, ordered by assignment_id.
    """
    due_dates: list[str] = _compute_due_dates()

    return (
        AssignmentDef(
            assignment_id="HW1",
            title="Variables, I/O, and Arithmetic",
            description=(
                "Practice basic variable declaration, user input/output, "
                "and arithmetic operations including integer and float "
                "math. Topics: print(), input(), type casting, operators."
            ),
            due_date=due_dates[0],
            max_score=100,
            num_test_cases=5,
            difficulty=1,
            required_files=("hw1_solution.py",),
        ),
        AssignmentDef(
            assignment_id="HW2",
            title="Conditionals and Boolean Logic",
            description=(
                "Implement programs using if/elif/else statements, "
                "comparison operators, and boolean expressions. Topics: "
                "branching, nested conditionals, logical operators."
            ),
            due_date=due_dates[1],
            max_score=100,
            num_test_cases=6,
            difficulty=2,
            required_files=("hw2_solution.py",),
        ),
        AssignmentDef(
            assignment_id="HW3",
            title="Loops and Iteration",
            description=(
                "Write programs using for loops, while loops, nested "
                "loops, and loop control statements (break, continue). "
                "Topics: counting, accumulation, sentinel loops."
            ),
            due_date=due_dates[2],
            max_score=100,
            num_test_cases=7,
            difficulty=3,
            required_files=("hw3_solution.py",),
        ),
        AssignmentDef(
            assignment_id="HW4",
            title="Functions and Modular Design",
            description=(
                "Define and call functions with parameters and return "
                "values. Practice function decomposition and code reuse. "
                "Topics: def, return, scope, helper functions."
            ),
            due_date=due_dates[3],
            max_score=100,
            num_test_cases=8,
            difficulty=4,
            required_files=("hw4_solution.py", "hw4_utils.py"),
        ),
        AssignmentDef(
            assignment_id="HW5",
            title="Lists and Data Structures",
            description=(
                "Manipulate lists using indexing, slicing, iteration, "
                "and built-in methods. Implement basic algorithms on "
                "lists. Topics: append, sort, comprehensions, 2D lists."
            ),
            due_date=due_dates[4],
            max_score=100,
            num_test_cases=8,
            difficulty=5,
            required_files=("hw5_solution.py", "hw5_utils.py"),
        ),
    )


def _build_test_cases() -> dict[str, tuple[TestCaseSpec, ...]]:
    """Build test case definitions for all 5 assignments.

    Each assignment has a specific number of test cases (5, 6, 7, 8, 8)
    with realistic CS1 problem inputs and expected outputs. Points are
    distributed evenly across test cases using _distribute_points().

    The test cases cover typical CS1 exercises:
        HW1: Arithmetic calculations (temperature conversion, area, etc.)
        HW2: Grade classification, leap year, eligibility checks
        HW3: Summation, factorial, Fibonacci, digit manipulation
        HW4: Primality, string reversal, palindrome, GCD
        HW5: List average, deduplication, sorting, merging

    Used by: module-level _TEST_CASES constant initialization.

    Returns:
        A dictionary mapping assignment_id to a tuple of TestCaseSpec
        instances. Keys: "HW1" through "HW5".
    """
    test_cases: dict[str, tuple[TestCaseSpec, ...]] = {}

    # ── HW1: Variables, I/O, and Arithmetic (5 test cases, 20 pts each) ──

    hw1_points: list[float] = _distribute_points(100, 5)
    test_cases["HW1"] = (
        TestCaseSpec(
            test_case_id="HW1_TC01",
            description="Add two integers: 3 + 5 = 8",
            input_data="3\n5\n",
            expected_output="8\n",
            points=hw1_points[0],
        ),
        TestCaseSpec(
            test_case_id="HW1_TC02",
            description="Convert 0 degrees Celsius to Fahrenheit (32.0)",
            input_data="0\n",
            expected_output="32.0\n",
            points=hw1_points[1],
        ),
        TestCaseSpec(
            test_case_id="HW1_TC03",
            description="Convert 100 degrees Celsius to Fahrenheit (212.0)",
            input_data="100\n",
            expected_output="212.0\n",
            points=hw1_points[2],
        ),
        TestCaseSpec(
            test_case_id="HW1_TC04",
            description="Calculate circle area with radius 5 (78.54)",
            input_data="5\n",
            expected_output="78.54\n",
            points=hw1_points[3],
        ),
        TestCaseSpec(
            test_case_id="HW1_TC05",
            description="Integer division and modulus: 17 / 5 = 3 rem 2",
            input_data="17\n5\n",
            expected_output="3\n2\n",
            points=hw1_points[4],
        ),
    )

    # ── HW2: Conditionals and Boolean Logic (6 test cases) ──

    hw2_points: list[float] = _distribute_points(100, 6)
    test_cases["HW2"] = (
        TestCaseSpec(
            test_case_id="HW2_TC01",
            description="Grade A for score >= 90 (input: 95)",
            input_data="95\n",
            expected_output="A\n",
            points=hw2_points[0],
        ),
        TestCaseSpec(
            test_case_id="HW2_TC02",
            description="Grade B for score 80-89 (input: 85)",
            input_data="85\n",
            expected_output="B\n",
            points=hw2_points[1],
        ),
        TestCaseSpec(
            test_case_id="HW2_TC03",
            description="Grade F for score < 60 (input: 45)",
            input_data="45\n",
            expected_output="F\n",
            points=hw2_points[2],
        ),
        TestCaseSpec(
            test_case_id="HW2_TC04",
            description="Leap year: 2024 is divisible by 4, not by 100",
            input_data="2024\n",
            expected_output="True\n",
            points=hw2_points[3],
        ),
        TestCaseSpec(
            test_case_id="HW2_TC05",
            description="Not a leap year: 1900 divisible by 100 not 400",
            input_data="1900\n",
            expected_output="False\n",
            points=hw2_points[4],
        ),
        TestCaseSpec(
            test_case_id="HW2_TC06",
            description="Leap year: 2000 is divisible by 400",
            input_data="2000\n",
            expected_output="True\n",
            points=hw2_points[5],
        ),
    )

    # ── HW3: Loops and Iteration (7 test cases) ──

    hw3_points: list[float] = _distribute_points(100, 7)
    test_cases["HW3"] = (
        TestCaseSpec(
            test_case_id="HW3_TC01",
            description="Sum of first 5 natural numbers: 1+2+3+4+5=15",
            input_data="5\n",
            expected_output="15\n",
            points=hw3_points[0],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC02",
            description="Factorial of 6: 6! = 720",
            input_data="6\n",
            expected_output="720\n",
            points=hw3_points[1],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC03",
            description="7th Fibonacci number (1-indexed): 13",
            input_data="7\n",
            expected_output="13\n",
            points=hw3_points[2],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC04",
            description="Count digits in 12345: 5 digits",
            input_data="12345\n",
            expected_output="5\n",
            points=hw3_points[3],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC05",
            description="Reverse the number 1234 -> 4321",
            input_data="1234\n",
            expected_output="4321\n",
            points=hw3_points[4],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC06",
            description="Sum of digits of 9876: 9+8+7+6=30",
            input_data="9876\n",
            expected_output="30\n",
            points=hw3_points[5],
        ),
        TestCaseSpec(
            test_case_id="HW3_TC07",
            description="Multiplication: 3 * 5 = 15",
            input_data="3\n5\n",
            expected_output="15\n",
            points=hw3_points[6],
        ),
    )

    # ── HW4: Functions and Modular Design (8 test cases) ──

    hw4_points: list[float] = _distribute_points(100, 8)
    test_cases["HW4"] = (
        TestCaseSpec(
            test_case_id="HW4_TC01",
            description="is_prime(7) returns True",
            input_data="7\n",
            expected_output="True\n",
            points=hw4_points[0],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC02",
            description="is_prime(4) returns False",
            input_data="4\n",
            expected_output="False\n",
            points=hw4_points[1],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC03",
            description="factorial(5) returns 120",
            input_data="5\n",
            expected_output="120\n",
            points=hw4_points[2],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC04",
            description="find_max([3,1,4,1,5]) returns 5",
            input_data="3 1 4 1 5\n",
            expected_output="5\n",
            points=hw4_points[3],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC05",
            description="reverse_string('hello') returns 'olleh'",
            input_data="hello\n",
            expected_output="olleh\n",
            points=hw4_points[4],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC06",
            description="is_palindrome('racecar') returns True",
            input_data="racecar\n",
            expected_output="True\n",
            points=hw4_points[5],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC07",
            description="power(2, 10) returns 1024",
            input_data="2\n10\n",
            expected_output="1024\n",
            points=hw4_points[6],
        ),
        TestCaseSpec(
            test_case_id="HW4_TC08",
            description="gcd(48, 18) returns 6",
            input_data="48\n18\n",
            expected_output="6\n",
            points=hw4_points[7],
        ),
    )

    # ── HW5: Lists and Data Structures (8 test cases) ──

    hw5_points: list[float] = _distribute_points(100, 8)
    test_cases["HW5"] = (
        TestCaseSpec(
            test_case_id="HW5_TC01",
            description="Average of [10, 20, 30] = 20.0",
            input_data="10 20 30\n",
            expected_output="20.0\n",
            points=hw5_points[0],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC02",
            description="Remove duplicates from [1, 2, 2, 3] -> [1, 2, 3]",
            input_data="1 2 2 3\n",
            expected_output="1 2 3\n",
            points=hw5_points[1],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC03",
            description="Sort [5, 3, 1, 4, 2] -> [1, 2, 3, 4, 5]",
            input_data="5 3 1 4 2\n",
            expected_output="1 2 3 4 5\n",
            points=hw5_points[2],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC04",
            description="Second largest in [3, 1, 4, 1, 5] = 4",
            input_data="3 1 4 1 5\n",
            expected_output="4\n",
            points=hw5_points[3],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC05",
            description="Count occurrences of 3 in [1, 3, 3, 3, 2] = 3",
            input_data="3\n1 3 3 3 2\n",
            expected_output="3\n",
            points=hw5_points[4],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC06",
            description="Merge sorted [1,3,5] and [2,4,6] -> [1,2,3,4,5,6]",
            input_data="1 3 5\n2 4 6\n",
            expected_output="1 2 3 4 5 6\n",
            points=hw5_points[5],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC07",
            description="List comprehension: squares of 1..4 -> 1 4 9 16",
            input_data="4\n",
            expected_output="1 4 9 16\n",
            points=hw5_points[6],
        ),
        TestCaseSpec(
            test_case_id="HW5_TC08",
            description="Flatten [[1,2],[3,4]] -> [1, 2, 3, 4]",
            input_data="1 2\n3 4\n",
            expected_output="1 2 3 4\n",
            points=hw5_points[7],
        ),
    )

    return test_cases


# ── Module-Level Constants ──────────────────────────────────────────────

# The 5 CS1 homework assignment definitions — the canonical source of
# assignment metadata for the entire seed data pipeline. All other
# modules import this constant rather than constructing AssignmentDef
# instances themselves.
#
# Tuple contents (in order):
#     HW1: Variables, I/O, and Arithmetic  (difficulty=1, 5 test cases)
#     HW2: Conditionals and Boolean Logic  (difficulty=2, 6 test cases)
#     HW3: Loops and Iteration             (difficulty=3, 7 test cases)
#     HW4: Functions and Modular Design    (difficulty=4, 8 test cases)
#     HW5: Lists and Data Structures       (difficulty=5, 8 test cases)
#
# Used by: generate_data.py (main loop iterates over ASSIGNMENTS),
#          code_generator.py (generates code per assignment),
#          grading_engine.py (uses num_test_cases and difficulty for scoring)
ASSIGNMENTS: tuple[AssignmentDef, ...] = _build_assignments()

# Private mapping of assignment_id to test case tuples.
# Populated once at module load time by _build_test_cases().
# Accessed via the public get_test_cases() function.
_TEST_CASES: dict[str, tuple[TestCaseSpec, ...]] = _build_test_cases()


# ── Public Query Functions ──────────────────────────────────────────────


def get_test_cases(assignment_id: str) -> tuple[TestCaseSpec, ...]:
    """Retrieve the test case definitions for a specific assignment.

    Looks up the pre-built test cases for the given assignment_id from
    the module-level _TEST_CASES dictionary. Each test case includes
    input data, expected output, and point value.

    Used by: grading_engine.py (to iterate over test cases when simulating
             execution results and computing scores),
             code_generator.py (to generate code that targets these inputs)

    Args:
        assignment_id: Assignment identifier string (e.g., "HW1", "HW3").
                       Must match one of the assignment IDs in ASSIGNMENTS.

    Returns:
        A tuple of TestCaseSpec instances for the specified assignment.

    Raises:
        ValueError: If assignment_id is not a recognized assignment
                    (not in ASSIGNMENTS).

    Example::

        test_cases = get_test_cases("HW1")
        assert len(test_cases) == 5
        assert sum(tc.points for tc in test_cases) == 100
    """
    if assignment_id not in _TEST_CASES:
        valid_ids: list[str] = sorted(_TEST_CASES.keys())
        raise ValueError(
            f"Unknown assignment_id: {assignment_id!r}. " f"Valid IDs: {valid_ids}"
        )
    return _TEST_CASES[assignment_id]


def get_assignment_by_id(assignment_id: str) -> AssignmentDef:
    """Retrieve a specific assignment definition by its ID.

    Convenience function for looking up a single AssignmentDef from
    the ASSIGNMENTS tuple without iterating manually.

    Used by: generate_data.py (when processing a single assignment),
             grading_engine.py (to get max_score and num_test_cases)

    Args:
        assignment_id: Assignment identifier string (e.g., "HW1").

    Returns:
        The AssignmentDef instance matching the given assignment_id.

    Raises:
        ValueError: If no assignment with the given ID exists in
                    ASSIGNMENTS.

    Example::

        hw3 = get_assignment_by_id("HW3")
        assert hw3.title == "Loops and Iteration"
        assert hw3.difficulty == 3
    """
    for assignment in ASSIGNMENTS:
        if assignment.assignment_id == assignment_id:
            return assignment

    valid_ids: list[str] = [a.assignment_id for a in ASSIGNMENTS]
    raise ValueError(
        f"Unknown assignment_id: {assignment_id!r}. " f"Valid IDs: {valid_ids}"
    )
