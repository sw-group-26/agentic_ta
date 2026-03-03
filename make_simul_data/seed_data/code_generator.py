"""Python code file generation for the seed data pipeline.

This module generates realistic Python source code files that simulate
student submissions for a CS1 course. Code quality varies based on the
student's skill level: high-skill students produce PEP8-compliant,
well-documented code, while low-skill students produce code with bugs,
poor style, and missing comments.

The generation approach is **Template + Variation + Error Injection**:
    1. Each assignment has 3 pre-written template variations.
    2. Each template has 3 quality tiers (high / medium / low).
    3. Style mutations add individuality on top of the selected template.
    4. Comment padding adjusts file size to the required 1-10 KB range.

Key exports:
    GeneratedCodeFile   -- Frozen dataclass holding one generated .py file.
    generate_code_files -- Main entry point: produces code files for a submission.

Module dependency graph:
    config.py      -->  code_generator.py  (FILE_SIZE_PYTHON, create_rng)
    students.py    -->  code_generator.py  (StudentProfile.skill_level)
    assignments.py -->  code_generator.py  (AssignmentDef.required_files)

Consumed by:
    submission_builder.py  (Step 5, packages generated files into ZIP)
    plagiarism.py          (Step 8, uses source text for similarity analysis)
    generate_data.py       (Step 10, main pipeline loop)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from make_simul_data.seed_data.config import (
    FILE_SIZE_PYTHON,
    AssignmentDef,
)
from make_simul_data.seed_data.students import StudentProfile

# ── Constants ────────────────────────────────────────────────────────

# Skill level threshold above which students produce high-quality code
# with PEP8 compliance, docstrings, type hints, and descriptive names.
# Used by: _select_quality_tier() in this module.
HIGH_SKILL_THRESHOLD: float = 0.8

# Skill level threshold below which students produce low-quality code
# containing intentional bugs (off-by-one, wrong operators, etc.).
# Students between LOW and HIGH thresholds produce medium-quality code
# that works correctly but has inconsistent style.
# Used by: _select_quality_tier() in this module.
LOW_SKILL_THRESHOLD: float = 0.5

# Effective skill boost per additional submission attempt.
# Simulates student learning: each retry improves code quality.
# Formula: effective_skill = min(1.0, skill + BOOST * (attempt - 1))
# Used by: _compute_effective_skill() in this module.
ATTEMPT_SKILL_BOOST: float = 0.1


# ── Data Structures ──────────────────────────────────────────────────


@dataclass(frozen=True)
class GeneratedCodeFile:
    """Immutable container for a single generated Python source file.

    Represents one .py file produced by the code generation pipeline.
    Each submission attempt produces 1-2 GeneratedCodeFile instances
    depending on the assignment's required_files (1 for HW1-HW3,
    2 for HW4-HW5).

    Created by: generate_code_files() in this module.
    Consumed by: submission_builder.py (Step 5, packaged into ZIP),
                 plagiarism.py (Step 8, source text for similarity),
                 generate_data.py (Step 10, main pipeline loop).

    Attributes:
        filename:   Name of the Python file (e.g., "hw1_solution.py",
                    "hw4_utils.py"). Must match one of the filenames
                    in AssignmentDef.required_files.
        content:    The full Python source code as a string, including
                    any docstrings, comments, and padding. This is the
                    raw text that will be written to disk.
        size_bytes: Length of content in bytes when UTF-8 encoded:
                    len(content.encode("utf-8")). Must fall within
                    FILE_SIZE_PYTHON range (1024-10240 bytes).
    """

    filename: str
    content: str
    size_bytes: int


@dataclass(frozen=True)
class CodeTemplate:
    """Immutable container for one code template variation.

    Each template represents one structural approach to solving the
    problems within an assignment. Multiple templates per assignment
    (3 variations) provide natural diversity across student submissions.
    Within each template, three quality levels (high / medium / low) are
    pre-written with different code style and bug characteristics.

    Created by: _build_hw*_templates() private functions in this module.
    Consumed by: _select_template() and generate_code_files().

    Attributes:
        template_id:    Unique identifier (e.g., "HW1_V1", "HW3_V3").
                        Used for logging and debugging, not persisted.
        assignment_id:  Which assignment this template belongs to
                        (e.g., "HW1"). Used to group templates in
                        the _TEMPLATES registry.
        high_quality:   Full source code string for a high-skill student
                        (skill > 0.8). Includes PEP8 formatting,
                        docstrings, descriptive names, and inline comments.
        medium_quality: Source code for a medium-skill student
                        (0.5 <= skill <= 0.8). Works correctly but with
                        inconsistent style, fewer comments, shorter names.
        low_quality:    Source code for a low-skill student (skill < 0.5).
                        Contains intentional bugs: off-by-one, wrong
                        operators, missing type conversions, etc.
        utils_high:     Optional utils file for high-skill (HW4, HW5 only).
                        None for HW1-HW3 which have no utils file.
        utils_medium:   Optional utils file for medium-skill.
        utils_low:      Optional utils file for low-skill.
    """

    template_id: str
    assignment_id: str
    high_quality: str
    medium_quality: str
    low_quality: str
    utils_high: str | None = None
    utils_medium: str | None = None
    utils_low: str | None = None


# ── Padding Comment Banks ────────────────────────────────────────────
# Collections of realistic student comments used to pad generated code
# to reach the FILE_SIZE_PYTHON minimum (1024 bytes). Different banks
# match different skill tiers to maintain realism.
# Used by: _pad_to_size() in this module.

_PADDING_COMMENTS_HIGH: tuple[str, ...] = (
    "# Note: I tested this with several edge cases and it handles them correctly.",
    "# The time complexity of this approach is O(n) which should be efficient.",
    "# I considered using a dictionary but a list works better for this problem.",
    "# Reference: Python documentation on built-in functions.",
    "# Alternative approach: could use list comprehension for a more Pythonic style.",
    "# This function follows the single-responsibility principle.",
    "# Edge case: empty input is handled by the default return value.",
    "# I initially used recursion but switched to iteration for better performance.",
    "# The variable naming convention follows PEP8 guidelines.",
    "# This implementation passes all test cases provided in the assignment.",
    "# I also tested with boundary values (0, negative numbers, very large inputs).",
    "# The math module is used for precise floating-point calculations.",
    "# Input validation ensures the program handles unexpected user input gracefully.",
    "# Each function has a docstring explaining its purpose and return value.",
    "# The main block ensures this file can be both imported and run directly.",
    "# I refactored the original monolithic code into smaller, testable functions.",
    "# Type hints are added to improve code readability and IDE support.",
    "# The algorithm uses early termination to avoid unnecessary computation.",
    "# I added comments explaining the mathematical formulas used.",
    "# This solution handles both integer and floating-point inputs correctly.",
    "# The output format matches exactly what the autograder expects.",
    "# I verified the results manually using a calculator before submitting.",
    "# The program structure follows the template provided in the lecture notes.",
    "# Error handling could be improved with try-except blocks in a future version.",
    "# The code is modular enough to be reused in future assignments.",
    "# I double-checked the rounding behavior for floating-point operations.",
    "# All functions are pure (no side effects) except for the I/O in main.",
    "# The logic was derived from the examples discussed in class.",
    "# I used Python 3 string formatting for cleaner output.",
    "# This version is cleaner than my first attempt which had redundant code.",
)

_PADDING_COMMENTS_MEDIUM: tuple[str, ...] = (
    "# this works but I'm not sure if there's a better way",
    "# tested with the examples from class",
    "# might need to fix this later",
    "# asked TA about this part",
    "# I think this is correct",
    "# not sure about edge cases",
    "# this was tricky to figure out",
    "# based on the textbook example",
    "# works for the test cases given",
    "# could probably simplify this",
    "# moved this into a function",
    "# changed the variable names to be clearer",
    "# this part took me a while",
    "# output matches the expected format",
    "# I had to look up how input() works",
    "# probably not the most efficient but it works",
    "# tried a different approach first but this is simpler",
    "# the formula is from the slides",
    "# fixed a bug where it was giving wrong answers",
    "# I hope the formatting is right",
)

_PADDING_COMMENTS_LOW: tuple[str, ...] = (
    "# idk if this is right",
    "# fix later",
    "# why doesnt this work",
    "# changed from last version",
    "# help",
    "# this keeps breaking",
    "# tried everything",
    "# almost works i think",
    "# not sure what this does",
    "# TODO fix this",
    "# it works sometimes",
    "# gave up on the other way",
    "# just need it to run",
    "# close enough",
    "# still getting errors",
)


# ── Private Helper Functions ─────────────────────────────────────────


def _compute_effective_skill(skill_level: float, attempt_no: int) -> float:
    """Compute effective skill level adjusted by submission attempt number.

    Later attempts simulate student learning: each retry improves the
    effective skill by ATTEMPT_SKILL_BOOST (0.1), capped at 1.0. This
    means a student with skill_level=0.65 on attempt 3 has an effective
    skill of min(1.0, 0.65 + 0.1 * 2) = 0.85.

    Used by: generate_code_files() in this module.

    Args:
        skill_level: Base skill from StudentProfile.skill_level (0.0-1.0).
        attempt_no:  Submission attempt number (1, 2, or 3).

    Returns:
        Adjusted skill level, clamped to [0.0, 1.0].
    """
    return min(1.0, skill_level + ATTEMPT_SKILL_BOOST * (attempt_no - 1))


def _select_quality_tier(effective_skill: float) -> str:
    """Determine code quality tier based on effective skill level.

    Maps the continuous effective_skill value to one of three discrete
    tiers that select which pre-written template variant to use:
        - "high"   (skill > 0.8): PEP8, docstrings, type hints
        - "medium" (0.5 <= skill <= 0.8): correct but poor style
        - "low"    (skill < 0.5): contains intentional bugs

    Used by: generate_code_files() in this module.

    Args:
        effective_skill: Adjusted skill level from _compute_effective_skill()
                         (0.0-1.0).

    Returns:
        One of "high", "medium", or "low".
    """
    if effective_skill > HIGH_SKILL_THRESHOLD:
        return "high"
    elif effective_skill >= LOW_SKILL_THRESHOLD:
        return "medium"
    else:
        return "low"


def _select_template(
    assignment_id: str,
    rng: random.Random,
) -> CodeTemplate:
    """Randomly select one code template variation for the given assignment.

    Each assignment has 3 template variations stored in _TEMPLATES.
    The RNG ensures reproducible, deterministic selection across runs
    with the same seed.

    Used by: generate_code_files() in this module.

    Args:
        assignment_id: Assignment ID (e.g., "HW1", "HW5").
        rng:           Seeded Random instance from config.create_rng().

    Returns:
        A CodeTemplate instance for the selected variation.

    Raises:
        ValueError: If assignment_id is not in _TEMPLATES (not HW1-HW5).
    """
    if assignment_id not in _TEMPLATES:
        valid_ids = sorted(_TEMPLATES.keys())
        raise ValueError(
            f"Unknown assignment_id: {assignment_id!r}. Valid IDs: {valid_ids}"
        )
    templates = _TEMPLATES[assignment_id]
    return rng.choice(templates)


def _apply_style_mutations(
    content: str,
    effective_skill: float,
    rng: random.Random,
) -> str:
    """Apply randomized cosmetic mutations to code for individuality.

    Mutations are non-functional changes that make each student's code
    look slightly different even when based on the same template. The
    intensity of mutations depends on the effective_skill tier:

    High skill: minor wording changes, blank line variations.
    Medium skill: remove some comments, inconsistent quoting.
    Low skill: remove most comments, add unused imports, debug prints.

    Used by: generate_code_files() in this module.

    Args:
        content:         The raw template code string to mutate.
        effective_skill: Adjusted skill level (drives mutation intensity).
        rng:             Seeded Random instance.

    Returns:
        The mutated code string with cosmetic variations applied.
    """
    lines = content.split("\n")
    mutated: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Decide whether to remove comment lines based on skill tier.
        # High-skill students keep all comments; low-skill students
        # lose most of them.
        if stripped.startswith("#") and not stripped.startswith("#!"):
            if effective_skill > HIGH_SKILL_THRESHOLD:
                # High skill: keep all comments, occasionally rephrase
                if rng.random() < 0.15:
                    line = line.replace("Calculate", "Compute")
                    line = line.replace("Return", "Get")
                    line = line.replace("Check", "Verify")
                mutated.append(line)
            elif effective_skill >= LOW_SKILL_THRESHOLD:
                # Medium skill: keep ~60% of comments
                if rng.random() < 0.60:
                    mutated.append(line)
            else:
                # Low skill: keep only ~25% of comments
                if rng.random() < 0.25:
                    mutated.append(line)
            continue

        # Randomly add or remove blank lines for structural variation.
        if stripped == "":
            if rng.random() < 0.3:
                continue  # Skip some blank lines
            mutated.append(line)
            continue

        mutated.append(line)

    # Low-skill students: occasionally add unused imports at the top.
    if effective_skill < LOW_SKILL_THRESHOLD and rng.random() < 0.5:
        unused_imports = ["import os", "import sys", "import time"]
        chosen = rng.choice(unused_imports)
        # Insert after any existing imports or at line 0.
        insert_idx = 0
        for i, ln in enumerate(mutated):
            if ln.strip().startswith("import ") or ln.strip().startswith("from "):
                insert_idx = i + 1
        mutated.insert(insert_idx, chosen)

    # Medium-skill students: occasionally swap quote styles in strings.
    if LOW_SKILL_THRESHOLD <= effective_skill <= HIGH_SKILL_THRESHOLD:
        for i, ln in enumerate(mutated):
            if rng.random() < 0.1 and '"""' not in ln:
                if '"' in ln and "'" not in ln:
                    mutated[i] = ln.replace('"', "'")

    return "\n".join(mutated)


def _pad_to_size(
    content: str,
    min_bytes: int,
    max_bytes: int,
    effective_skill: float,
    rng: random.Random,
) -> str:
    """Pad or trim code content to fall within the target byte range.

    If content is below min_bytes, appends comment blocks with
    realistic-looking student notes selected from the appropriate
    padding comment bank. If content exceeds max_bytes, trims
    trailing comment lines (never removes functional code).

    Used by: generate_code_files() in this module.

    Args:
        content:         The source code string to adjust.
        min_bytes:       Minimum target size (FILE_SIZE_PYTHON[0] = 1024).
        max_bytes:       Maximum target size (FILE_SIZE_PYTHON[1] = 10240).
        effective_skill: Skill level for selecting the comment bank.
        rng:             Seeded Random instance for selecting padding.

    Returns:
        The adjusted code string within [min_bytes, max_bytes].
    """
    current_size = len(content.encode("utf-8"))

    # Select the appropriate comment bank based on skill tier.
    if effective_skill > HIGH_SKILL_THRESHOLD:
        bank = _PADDING_COMMENTS_HIGH
    elif effective_skill >= LOW_SKILL_THRESHOLD:
        bank = _PADDING_COMMENTS_MEDIUM
    else:
        bank = _PADDING_COMMENTS_LOW

    # Pad up to min_bytes by appending randomly selected comments.
    if current_size < min_bytes:
        padding_lines: list[str] = [
            "",
            "",
            "# " + "=" * 60,
            "# Student Notes",
            "# " + "=" * 60,
        ]
        while current_size < min_bytes:
            comment = rng.choice(bank)
            padding_lines.append(comment)
            current_size = len(
                (content + "\n" + "\n".join(padding_lines)).encode("utf-8")
            )
        content = content + "\n" + "\n".join(padding_lines) + "\n"

    # Trim trailing comment lines if above max_bytes.
    # Only trim lines that start with '#' or are blank to avoid
    # removing functional code.
    lines = content.split("\n")
    current_size = len(content.encode("utf-8"))
    while current_size > max_bytes and len(lines) > 10:
        last_line = lines[-1].strip()
        if last_line == "" or last_line.startswith("#"):
            lines.pop()
            content = "\n".join(lines)
            current_size = len(content.encode("utf-8"))
        else:
            break  # Stop if we hit functional code

    return content


# ── HW1 Templates: Variables, I/O, and Arithmetic ───────────────────
# Problems (from test cases in assignments.py):
#   TC01: Add two integers (3 + 5 = 8)
#   TC02: Celsius to Fahrenheit (0 -> 32.0)
#   TC03: Celsius to Fahrenheit (100 -> 212.0)
#   TC04: Circle area with radius (5 -> 78.54)
#   TC05: Integer division and modulus (17 / 5 = 3 rem 2)


def _build_hw1_templates() -> tuple[CodeTemplate, ...]:
    """Build 3 code template variations for HW1 (Variables, I/O, Arithmetic).

    Each variation covers all 5 test case problems but organizes the
    code differently: V1 uses helper functions, V2 uses inline math,
    V3 uses a menu-driven approach. All variations read from stdin
    and print to stdout to match the test case input/output format.

    Used by: module-level _TEMPLATES dict initialization.

    Returns:
        Tuple of 3 CodeTemplate instances for HW1.
    """
    # ── Variation 1: Helper functions approach ──
    v1_high = '''\
"""HW1 Solution: Variables, I/O, and Arithmetic Operations.

This module implements basic arithmetic operations including
addition, temperature conversion, area calculation, and
integer division with modulus.

Author: Student
Course: CS1 - Introduction to Computer Science
"""

import math


def add_two_numbers(a: int, b: int) -> int:
    """Return the sum of two integers.

    Args:
        a: First integer operand.
        b: Second integer operand.

    Returns:
        The sum a + b.
    """
    return a + b


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert a temperature from Celsius to Fahrenheit.

    Uses the standard formula: F = C * 9/5 + 32

    Args:
        celsius: Temperature in degrees Celsius.

    Returns:
        Temperature in degrees Fahrenheit.
    """
    return celsius * 9 / 5 + 32


def circle_area(radius: float) -> float:
    """Calculate the area of a circle given its radius.

    Uses math.pi for precision and rounds to 2 decimal places.

    Args:
        radius: The radius of the circle.

    Returns:
        The area of the circle, rounded to 2 decimal places.
    """
    return round(math.pi * radius ** 2, 2)


def integer_division(a: int, b: int) -> tuple[int, int]:
    """Perform integer division and return quotient and remainder.

    Args:
        a: The dividend.
        b: The divisor.

    Returns:
        A tuple of (quotient, remainder).
    """
    return a // b, a % b


def main() -> None:
    """Main function to run all arithmetic problems."""
    # Problem 1: Add two integers
    x = int(input())
    y = int(input())
    print(add_two_numbers(x, y))

    # Problem 2-3: Celsius to Fahrenheit conversion
    celsius = float(input())
    print(celsius_to_fahrenheit(celsius))

    # Problem 4: Circle area calculation
    radius = float(input())
    print(circle_area(radius))

    # Problem 5: Integer division and modulus
    dividend = int(input())
    divisor = int(input())
    quotient, remainder = integer_division(dividend, divisor)
    print(quotient)
    print(remainder)


if __name__ == "__main__":
    main()
'''

    v1_medium = """\
import math

def add(a, b):
    return a + b

def c_to_f(c):
    return c * 9/5 + 32

def area(r):
    return round(math.pi * r**2, 2)

def div(a, b):
    return a // b, a % b

if __name__ == "__main__":
    x = int(input())
    y = int(input())
    print(add(x, y))

    c = float(input())
    print(c_to_f(c))

    r = float(input())
    print(area(r))

    a = int(input())
    b = int(input())
    q, rem = div(a, b)
    print(q)
    print(rem)
"""

    v1_low = """\
import math

def add(a, b):
    return a + b

def c_to_f(c):
    # Bug: integer division instead of float division
    return c * 9//5 + 32

def area(r):
    # Bug: uses approximate pi, no rounding
    return 3.14 * r * r

def div(a, b):
    # Bug: swapped quotient and remainder
    return a % b, a // b

x = int(input())
y = int(input())
print(add(x, y))
c = int(input())
print(c_to_f(c))
r = float(input())
print(area(r))
a = int(input())
b = int(input())
q, r = div(a, b)
print(q)
print(r)
"""

    # ── Variation 2: Inline computation approach ──
    v2_high = '''\
"""HW1 Solution: Variables, I/O, and Arithmetic.

Demonstrates basic Python operations: integer arithmetic,
floating-point conversion, mathematical constants, and
the modulo operator.
"""

import math


def main() -> None:
    """Execute all arithmetic problems sequentially."""
    # Problem 1: Read two integers and print their sum.
    num1: int = int(input())
    num2: int = int(input())
    total: int = num1 + num2
    print(total)

    # Problem 2-3: Convert Celsius to Fahrenheit.
    # Formula: F = C * (9/5) + 32
    temp_celsius: float = float(input())
    temp_fahrenheit: float = temp_celsius * 9 / 5 + 32
    print(temp_fahrenheit)

    # Problem 4: Calculate circle area using A = pi * r^2.
    radius: float = float(input())
    area: float = round(math.pi * radius ** 2, 2)
    print(area)

    # Problem 5: Integer division and modulus.
    dividend: int = int(input())
    divisor: int = int(input())
    print(dividend // divisor)
    print(dividend % divisor)


if __name__ == "__main__":
    main()
'''

    v2_medium = """\
import math

num1 = int(input())
num2 = int(input())
print(num1 + num2)

temp = float(input())
print(temp * 9/5 + 32)

r = float(input())
print(round(math.pi * r**2, 2))

a = int(input())
b = int(input())
print(a // b)
print(a % b)
"""

    v2_low = """\
num1 = int(input())
num2 = int(input())
print(num1 + num2)

# Bug: reads as int instead of float
temp = int(input())
# Bug: wrong formula with integer division
print(temp * 9//5 + 32)

r = float(input())
# Bug: wrong pi value and no rounding
print(3.14 * r * r)

a = int(input())
b = int(input())
# Bug: regular division instead of integer division
print(a / b)
print(a % b)
"""

    # ── Variation 3: Dictionary-dispatch approach ──
    v3_high = '''\
"""HW1 Solution: Variables, I/O, and Arithmetic Operations.

This module uses a structured approach with named functions
for each arithmetic problem. Each function reads its own
input and prints the result.
"""

import math


def problem_addition() -> None:
    """Read two integers and print their sum."""
    a: int = int(input())
    b: int = int(input())
    result: int = a + b
    print(result)


def problem_celsius_to_fahrenheit() -> None:
    """Read a Celsius temperature and print it in Fahrenheit.

    Formula: F = C * 9/5 + 32
    """
    celsius: float = float(input())
    fahrenheit: float = celsius * 9.0 / 5.0 + 32.0
    print(fahrenheit)


def problem_circle_area() -> None:
    """Read a radius and print the area of the circle.

    Uses math.pi for maximum precision, rounded to 2 decimal places.
    """
    radius: float = float(input())
    area: float = round(math.pi * radius ** 2, 2)
    print(area)


def problem_integer_division() -> None:
    """Read two integers and print quotient and remainder."""
    a: int = int(input())
    b: int = int(input())
    print(a // b)
    print(a % b)


def main() -> None:
    """Run all problems in sequence."""
    problem_addition()
    problem_celsius_to_fahrenheit()
    problem_circle_area()
    problem_integer_division()


if __name__ == "__main__":
    main()
'''

    v3_medium = """\
import math

def do_add():
    a = int(input())
    b = int(input())
    print(a + b)

def do_convert():
    c = float(input())
    print(c * 9/5 + 32)

def do_area():
    r = float(input())
    print(round(math.pi * r**2, 2))

def do_div():
    a = int(input())
    b = int(input())
    print(a // b)
    print(a % b)

if __name__ == "__main__":
    do_add()
    do_convert()
    do_area()
    do_div()
"""

    v3_low = """\
import math

def do_add():
    a = int(input())
    b = int(input())
    print(a + b)

def do_convert():
    # Bug: forgot to convert to float
    c = int(input())
    print(c * 9//5 + 32)

def do_area():
    r = float(input())
    # Bug: uses wrong constant
    print(3.14 * r * r)

def do_div():
    a = int(input())
    b = int(input())
    # Bug: prints remainder before quotient
    print(a % b)
    print(a // b)

do_add()
do_convert()
do_area()
do_div()
"""

    return (
        CodeTemplate(
            template_id="HW1_V1",
            assignment_id="HW1",
            high_quality=v1_high,
            medium_quality=v1_medium,
            low_quality=v1_low,
        ),
        CodeTemplate(
            template_id="HW1_V2",
            assignment_id="HW1",
            high_quality=v2_high,
            medium_quality=v2_medium,
            low_quality=v2_low,
        ),
        CodeTemplate(
            template_id="HW1_V3",
            assignment_id="HW1",
            high_quality=v3_high,
            medium_quality=v3_medium,
            low_quality=v3_low,
        ),
    )


# ── HW2 Templates: Conditionals and Boolean Logic ───────────────────
# Problems (from test cases in assignments.py):
#   TC01: Grade A for score >= 90 (95 -> "A")
#   TC02: Grade B for score 80-89 (85 -> "B")
#   TC03: Grade F for score < 60 (45 -> "F")
#   TC04: Leap year 2024 -> True
#   TC05: Not leap year 1900 -> False
#   TC06: Leap year 2000 -> True


def _build_hw2_templates() -> tuple[CodeTemplate, ...]:
    """Build 3 code template variations for HW2 (Conditionals, Boolean Logic).

    Covers grade classification (A/B/C/D/F) and leap year determination.
    Variations differ in conditional structure: V1 uses if/elif chains,
    V2 uses nested ifs, V3 uses a function-based approach.

    Used by: module-level _TEMPLATES dict initialization.

    Returns:
        Tuple of 3 CodeTemplate instances for HW2.
    """
    v1_high = '''\
"""HW2 Solution: Conditionals and Boolean Logic.

This module implements grade classification based on numeric scores
and leap year determination using conditional statements.

Author: Student
Course: CS1 - Introduction to Computer Science
"""


def classify_grade(score: int) -> str:
    """Classify a numeric score into a letter grade.

    Grading scale:
        A: score >= 90
        B: 80 <= score < 90
        C: 70 <= score < 80
        D: 60 <= score < 70
        F: score < 60

    Args:
        score: Numeric score (0-100).

    Returns:
        A single letter grade string ("A", "B", "C", "D", or "F").
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def is_leap_year(year: int) -> bool:
    """Determine whether a given year is a leap year.

    A year is a leap year if:
        1. It is divisible by 4, AND
        2. It is NOT divisible by 100, UNLESS
        3. It is also divisible by 400.

    Args:
        year: The year to check (positive integer).

    Returns:
        True if the year is a leap year, False otherwise.
    """
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False


def main() -> None:
    """Main function: read inputs and print results."""
    # Grade classification
    score: int = int(input())
    print(classify_grade(score))

    # Leap year check
    year: int = int(input())
    print(is_leap_year(year))


if __name__ == "__main__":
    main()
'''

    v1_medium = """\
def grade(score):
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def leap(year):
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    if year % 4 == 0:
        return True
    return False

score = int(input())
print(grade(score))
year = int(input())
print(leap(year))
"""

    v1_low = """\
def grade(score):
    if score >= 90:
        return "A"
    # Bug: missing elif for B, uses > instead of >=
    elif score > 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"

def leap(year):
    # Bug: missing the 400 rule
    if year % 4 == 0:
        if year % 100 == 0:
            return False
        return True
    return False

score = int(input())
print(grade(score))
year = int(input())
print(leap(year))
"""

    # ── Variation 2: Nested conditionals ──
    v2_high = '''\
"""HW2 Solution: Conditionals and Boolean Logic.

Implements grade classification and leap year checking
using structured conditional expressions.
"""


def get_letter_grade(score: int) -> str:
    """Convert a numeric score to a letter grade.

    Args:
        score: Integer score from 0 to 100.

    Returns:
        Letter grade as a string.
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def check_leap_year(year: int) -> bool:
    """Check if a year is a leap year using the Gregorian calendar rules.

    Args:
        year: The year to evaluate.

    Returns:
        True if leap year, False otherwise.
    """
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


def main() -> None:
    """Run grade and leap year programs."""
    score: int = int(input())
    print(get_letter_grade(score))

    year: int = int(input())
    print(check_leap_year(year))


if __name__ == "__main__":
    main()
'''

    v2_medium = """\
def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    elif s >= 60:
        return "D"
    else:
        return "F"

def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))
"""

    v2_low = """\
def get_grade(s):
    if s >= 90:
        return "A"
    elif s >= 80:
        return "B"
    elif s >= 70:
        return "C"
    # Bug: missing D grade, jumps to F
    else:
        return "F"

def is_leap(y):
    # Bug: wrong logic - OR instead of AND
    return y % 4 == 0 or y % 100 != 0

s = int(input())
print(get_grade(s))
y = int(input())
print(is_leap(y))
"""

    # ── Variation 3: Single-expression approach ──
    v3_high = '''\
"""HW2 Solution: Conditionals and Boolean Logic.

Uses clear function decomposition for grade classification
and leap year determination.
"""


def assign_grade(score: int) -> str:
    """Assign a letter grade based on the score.

    Grading thresholds: A>=90, B>=80, C>=70, D>=60, F<60.

    Args:
        score: The numeric score to classify.

    Returns:
        The corresponding letter grade.
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    return "F"


def is_leap_year(year: int) -> bool:
    """Determine whether the given year is a leap year.

    Leap year rules:
        - Divisible by 4 AND not by 100, OR divisible by 400.

    Args:
        year: Calendar year as a positive integer.

    Returns:
        True if the year is a leap year.
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def main() -> None:
    """Entry point: process grade and leap year inputs."""
    score: int = int(input())
    print(assign_grade(score))

    year: int = int(input())
    print(is_leap_year(year))


if __name__ == "__main__":
    main()
'''

    v3_medium = """\
def assign_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"

def is_leap(year):
    if year % 400 == 0: return True
    if year % 100 == 0: return False
    return year % 4 == 0

score = int(input())
print(assign_grade(score))
year = int(input())
print(is_leap(year))
"""

    v3_low = """\
def assign_grade(score):
    # Bug: wrong boundary - uses > instead of >=
    if score > 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"

def is_leap(year):
    # Bug: only checks divisible by 4
    if year % 4 == 0:
        return True
    return False

score = int(input())
print(assign_grade(score))
year = int(input())
print(is_leap(year))
"""

    return (
        CodeTemplate(
            template_id="HW2_V1",
            assignment_id="HW2",
            high_quality=v1_high,
            medium_quality=v1_medium,
            low_quality=v1_low,
        ),
        CodeTemplate(
            template_id="HW2_V2",
            assignment_id="HW2",
            high_quality=v2_high,
            medium_quality=v2_medium,
            low_quality=v2_low,
        ),
        CodeTemplate(
            template_id="HW2_V3",
            assignment_id="HW2",
            high_quality=v3_high,
            medium_quality=v3_medium,
            low_quality=v3_low,
        ),
    )


# ── HW3 Templates: Loops and Iteration ──────────────────────────────
# Problems (from test cases in assignments.py):
#   TC01: Sum of first N natural numbers (5 -> 15)
#   TC02: Factorial of N (6 -> 720)
#   TC03: Nth Fibonacci number, 1-indexed (7 -> 13)
#   TC04: Count digits in a number (12345 -> 5)
#   TC05: Reverse a number (1234 -> 4321)
#   TC06: Sum of digits (9876 -> 30)
#   TC07: Multiply two numbers using loop (3 * 5 = 15)


def _build_hw3_templates() -> tuple[CodeTemplate, ...]:
    """Build 3 code template variations for HW3 (Loops and Iteration).

    Covers summation, factorial, Fibonacci, digit operations, and
    multiplication using loops. Variations differ in loop style:
    V1 uses for loops, V2 uses while loops, V3 mixes both.

    Used by: module-level _TEMPLATES dict initialization.

    Returns:
        Tuple of 3 CodeTemplate instances for HW3.
    """
    v1_high = '''\
"""HW3 Solution: Loops and Iteration.

This module demonstrates various loop-based algorithms including
summation, factorial, Fibonacci, and digit manipulation.

Author: Student
Course: CS1 - Introduction to Computer Science
"""


def sum_natural(n: int) -> int:
    """Calculate the sum of the first n natural numbers.

    Uses a for loop to accumulate 1 + 2 + ... + n.

    Args:
        n: Upper bound (positive integer).

    Returns:
        Sum of integers from 1 to n inclusive.
    """
    total: int = 0
    for i in range(1, n + 1):
        total += i
    return total


def factorial(n: int) -> int:
    """Calculate n! (n factorial) iteratively.

    Args:
        n: Non-negative integer.

    Returns:
        The factorial of n (n! = 1 * 2 * ... * n).
    """
    result: int = 1
    for i in range(1, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (1-indexed).

    Sequence: 1, 1, 2, 3, 5, 8, 13, ...
    fibonacci(1) = 1, fibonacci(7) = 13.

    Args:
        n: Position in the Fibonacci sequence (1-indexed).

    Returns:
        The nth Fibonacci number.
    """
    if n <= 2:
        return 1
    a: int = 1
    b: int = 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b


def count_digits(number: int) -> int:
    """Count the number of digits in an integer.

    Args:
        number: A positive integer.

    Returns:
        The number of digits.
    """
    count: int = 0
    while number > 0:
        number //= 10
        count += 1
    return count


def reverse_number(number: int) -> int:
    """Reverse the digits of a positive integer.

    Example: 1234 -> 4321

    Args:
        number: A positive integer to reverse.

    Returns:
        The reversed number.
    """
    reversed_num: int = 0
    while number > 0:
        reversed_num = reversed_num * 10 + number % 10
        number //= 10
    return reversed_num


def sum_digits(number: int) -> int:
    """Calculate the sum of digits of a positive integer.

    Args:
        number: A positive integer.

    Returns:
        Sum of all digits.
    """
    total: int = 0
    while number > 0:
        total += number % 10
        number //= 10
    return total


def multiply(a: int, b: int) -> int:
    """Multiply two integers using repeated addition.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        The product a * b.
    """
    result: int = 0
    for _ in range(b):
        result += a
    return result


def main() -> None:
    """Main function to execute all loop problems."""
    # Problem 1: Sum of first N natural numbers
    n1: int = int(input())
    print(sum_natural(n1))

    # Problem 2: Factorial
    n2: int = int(input())
    print(factorial(n2))

    # Problem 3: Fibonacci
    n3: int = int(input())
    print(fibonacci(n3))

    # Problem 4: Count digits
    n4: int = int(input())
    print(count_digits(n4))

    # Problem 5: Reverse number
    n5: int = int(input())
    print(reverse_number(n5))

    # Problem 6: Sum of digits
    n6: int = int(input())
    print(sum_digits(n6))

    # Problem 7: Multiply two numbers
    a: int = int(input())
    b: int = int(input())
    print(multiply(a, b))


if __name__ == "__main__":
    main()
'''

    v1_medium = """\
def sum_n(n):
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

def fact(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def fib(n):
    if n <= 2:
        return 1
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b

def count_dig(num):
    count = 0
    while num > 0:
        num //= 10
        count += 1
    return count

def rev_num(num):
    rev = 0
    while num > 0:
        rev = rev * 10 + num % 10
        num //= 10
    return rev

def sum_dig(num):
    total = 0
    while num > 0:
        total += num % 10
        num //= 10
    return total

def mult(a, b):
    result = 0
    for _ in range(b):
        result += a
    return result

n = int(input())
print(sum_n(n))
n = int(input())
print(fact(n))
n = int(input())
print(fib(n))
n = int(input())
print(count_dig(n))
n = int(input())
print(rev_num(n))
n = int(input())
print(sum_dig(n))
a = int(input())
b = int(input())
print(mult(a, b))
"""

    v1_low = """\
def sum_n(n):
    total = 0
    # Bug: range(1, n) instead of range(1, n+1) - off by one
    for i in range(1, n):
        total += i
    return total

def fact(n):
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def fib(n):
    # Bug: wrong initial values
    a, b = 0, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a

def count_dig(num):
    count = 0
    while num > 0:
        num //= 10
        count += 1
    return count

def rev_num(num):
    rev = 0
    while num > 0:
        rev = rev * 10 + num % 10
        num //= 10
    return rev

def sum_dig(num):
    total = 0
    while num > 0:
        total += num % 10
        num //= 10
    return total

def mult(a, b):
    # Bug: starts from a instead of 0
    result = a
    for _ in range(b):
        result += a
    return result

n = int(input())
print(sum_n(n))
n = int(input())
print(fact(n))
n = int(input())
print(fib(n))
n = int(input())
print(count_dig(n))
n = int(input())
print(rev_num(n))
n = int(input())
print(sum_dig(n))
a = int(input())
b = int(input())
print(mult(a, b))
"""

    v2_high = '''\
"""HW3 Solution: Loops and Iteration.

Implements loop-based algorithms using while loops.
"""


def sum_of_natural_numbers(n: int) -> int:
    """Sum 1 + 2 + ... + n using a while loop."""
    total: int = 0
    i: int = 1
    while i <= n:
        total += i
        i += 1
    return total


def compute_factorial(n: int) -> int:
    """Compute n! iteratively."""
    result: int = 1
    i: int = 1
    while i <= n:
        result *= i
        i += 1
    return result


def get_fibonacci(n: int) -> int:
    """Get the nth Fibonacci number (1-indexed)."""
    if n <= 2:
        return 1
    prev: int = 1
    curr: int = 1
    count: int = 2
    while count < n:
        prev, curr = curr, prev + curr
        count += 1
    return curr


def digit_count(number: int) -> int:
    """Count digits in a positive integer."""
    count: int = 0
    while number > 0:
        number //= 10
        count += 1
    return count


def reverse_digits(number: int) -> int:
    """Reverse the digits of a number."""
    result: int = 0
    while number > 0:
        result = result * 10 + number % 10
        number //= 10
    return result


def digit_sum(number: int) -> int:
    """Sum all digits of a number."""
    total: int = 0
    while number > 0:
        total += number % 10
        number //= 10
    return total


def loop_multiply(a: int, b: int) -> int:
    """Multiply using repeated addition."""
    product: int = 0
    i: int = 0
    while i < b:
        product += a
        i += 1
    return product


def main() -> None:
    """Run all problems."""
    print(sum_of_natural_numbers(int(input())))
    print(compute_factorial(int(input())))
    print(get_fibonacci(int(input())))
    print(digit_count(int(input())))
    print(reverse_digits(int(input())))
    print(digit_sum(int(input())))
    a: int = int(input())
    b: int = int(input())
    print(loop_multiply(a, b))


if __name__ == "__main__":
    main()
'''

    v2_medium = """\
def sum_n(n):
    total = 0
    i = 1
    while i <= n:
        total += i
        i += 1
    return total

def fact(n):
    result = 1
    i = 1
    while i <= n:
        result *= i
        i += 1
    return result

def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    i = 2
    while i < n:
        a, b = b, a + b
        i += 1
    return b

def digits(num):
    c = 0
    while num > 0:
        num //= 10
        c += 1
    return c

def rev(num):
    r = 0
    while num > 0:
        r = r * 10 + num % 10
        num //= 10
    return r

def dsum(num):
    s = 0
    while num > 0:
        s += num % 10
        num //= 10
    return s

def mul(a, b):
    r = 0
    i = 0
    while i < b:
        r += a
        i += 1
    return r

print(sum_n(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(digits(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))
"""

    v2_low = """\
def sum_n(n):
    total = 0
    i = 1
    # Bug: < instead of <=
    while i < n:
        total += i
        i += 1
    return total

def fact(n):
    # Bug: starts result at 0 instead of 1
    result = 0
    i = 1
    while i <= n:
        result *= i
        i += 1
    return result

def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    i = 2
    while i < n:
        a, b = b, a + b
        i += 1
    return b

def digits(num):
    c = 0
    while num > 0:
        num //= 10
        c += 1
    return c

def rev(num):
    r = 0
    while num > 0:
        r = r * 10 + num % 10
        num //= 10
    return r

def dsum(num):
    s = 0
    while num > 0:
        s += num % 10
        num //= 10
    return s

def mul(a, b):
    # Bug: off-by-one (adds a once too many)
    r = a
    i = 0
    while i < b:
        r += a
        i += 1
    return r

print(sum_n(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(digits(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))
"""

    v3_high = '''\
"""HW3 Solution: Loops and Iteration.

A clean implementation using for-loops and while-loops
for various numeric algorithms.
"""


def natural_sum(n: int) -> int:
    """Return the sum of integers from 1 to n."""
    return sum(range(1, n + 1))


def factorial(n: int) -> int:
    """Return n factorial computed iteratively."""
    result: int = 1
    for i in range(2, n + 1):
        result *= i
    return result


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number (1-indexed)."""
    if n <= 2:
        return 1
    a: int = 1
    b: int = 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b


def count_digits(num: int) -> int:
    """Count digits by converting to string."""
    return len(str(num))


def reverse_number(num: int) -> int:
    """Reverse digits using modular arithmetic."""
    result: int = 0
    while num > 0:
        result = result * 10 + num % 10
        num //= 10
    return result


def digit_sum(num: int) -> int:
    """Sum of all digits in a number."""
    total: int = 0
    while num > 0:
        total += num % 10
        num //= 10
    return total


def repeated_add(a: int, b: int) -> int:
    """Multiply via repeated addition."""
    result: int = 0
    for _ in range(b):
        result += a
    return result


def main() -> None:
    """Execute all loop problems in order."""
    print(natural_sum(int(input())))
    print(factorial(int(input())))
    print(fibonacci(int(input())))
    print(count_digits(int(input())))
    print(reverse_number(int(input())))
    print(digit_sum(int(input())))
    a: int = int(input())
    b: int = int(input())
    print(repeated_add(a, b))


if __name__ == "__main__":
    main()
'''

    v3_medium = """\
def nat_sum(n):
    return sum(range(1, n + 1))

def fact(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r

def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b

def cnt_dig(num):
    return len(str(num))

def rev(num):
    r = 0
    while num > 0:
        r = r * 10 + num % 10
        num //= 10
    return r

def dsum(num):
    s = 0
    while num > 0:
        s += num % 10
        num //= 10
    return s

def mul(a, b):
    r = 0
    for _ in range(b):
        r += a
    return r

print(nat_sum(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(cnt_dig(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))
"""

    v3_low = """\
def nat_sum(n):
    # Bug: starts from 0 and uses range(n) which sums 0..n-1
    return sum(range(n))

def fact(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r

def fib(n):
    if n <= 2: return 1
    a, b = 1, 1
    for _ in range(n - 2):
        a, b = b, a + b
    return b

def cnt_dig(num):
    return len(str(num))

def rev(num):
    r = 0
    while num > 0:
        r = r * 10 + num % 10
        num //= 10
    return r

def dsum(num):
    s = 0
    while num > 0:
        s += num % 10
        num //= 10
    return s

def mul(a, b):
    # Bug: multiplies a*b then adds a again
    r = a
    for _ in range(b):
        r += a
    return r

print(nat_sum(int(input())))
print(fact(int(input())))
print(fib(int(input())))
print(cnt_dig(int(input())))
print(rev(int(input())))
print(dsum(int(input())))
a = int(input())
b = int(input())
print(mul(a, b))
"""

    return (
        CodeTemplate(
            template_id="HW3_V1",
            assignment_id="HW3",
            high_quality=v1_high,
            medium_quality=v1_medium,
            low_quality=v1_low,
        ),
        CodeTemplate(
            template_id="HW3_V2",
            assignment_id="HW3",
            high_quality=v2_high,
            medium_quality=v2_medium,
            low_quality=v2_low,
        ),
        CodeTemplate(
            template_id="HW3_V3",
            assignment_id="HW3",
            high_quality=v3_high,
            medium_quality=v3_medium,
            low_quality=v3_low,
        ),
    )


# ── HW4 Templates: Functions and Modular Design ─────────────────────
# Problems (from test cases in assignments.py):
#   TC01: is_prime(7) -> True
#   TC02: is_prime(4) -> False
#   TC03: factorial(5) -> 120
#   TC04: find_max([3,1,4,1,5]) -> 5
#   TC05: reverse_string("hello") -> "olleh"
#   TC06: is_palindrome("racecar") -> True
#   TC07: power(2, 10) -> 1024
#   TC08: gcd(48, 18) -> 6
# Files: hw4_solution.py + hw4_utils.py


def _build_hw4_templates() -> tuple[CodeTemplate, ...]:
    """Build 3 code template variations for HW4 (Functions, Modular Design).

    Each variation splits logic between hw4_solution.py (main driver)
    and hw4_utils.py (utility functions). Variations differ in which
    functions go in utils, algorithm choices (iterative vs recursive),
    and code organization.

    Used by: module-level _TEMPLATES dict initialization.

    Returns:
        Tuple of 3 CodeTemplate instances for HW4 (with utils files).
    """
    # ── Variation 1: All helpers in utils ──
    v1_utils_high = '''\
"""HW4 Utility Functions: Reusable helper functions.

This module provides mathematical and string utility functions
used by the main hw4_solution.py driver.
"""


def is_prime(n: int) -> bool:
    """Check if a number is prime.

    A prime number is greater than 1 and has no divisors other
    than 1 and itself. Uses trial division up to sqrt(n).

    Args:
        n: Integer to check.

    Returns:
        True if n is prime, False otherwise.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    i: int = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def factorial(n: int) -> int:
    """Compute n! iteratively.

    Args:
        n: Non-negative integer.

    Returns:
        n factorial.
    """
    result: int = 1
    for i in range(2, n + 1):
        result *= i
    return result


def find_max(numbers: list[int]) -> int:
    """Find the maximum value in a list of integers.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        The largest integer in the list.
    """
    max_val: int = numbers[0]
    for num in numbers[1:]:
        if num > max_val:
            max_val = num
    return max_val


def reverse_string(text: str) -> str:
    """Reverse a string.

    Args:
        text: The string to reverse.

    Returns:
        The reversed string.
    """
    return text[::-1]


def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome.

    Args:
        text: The string to check.

    Returns:
        True if text reads the same forwards and backwards.
    """
    return text == text[::-1]


def power(base: int, exponent: int) -> int:
    """Compute base raised to the exponent using a loop.

    Args:
        base: The base number.
        exponent: The exponent (non-negative integer).

    Returns:
        base ** exponent.
    """
    result: int = 1
    for _ in range(exponent):
        result *= base
    return result


def gcd(a: int, b: int) -> int:
    """Compute the greatest common divisor using Euclid's algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.

    Returns:
        The GCD of a and b.
    """
    while b != 0:
        a, b = b, a % b
    return a
'''

    v1_high = '''\
"""HW4 Solution: Functions and Modular Design.

This module serves as the main driver that reads input and calls
utility functions defined in hw4_utils.py.
"""

from hw4_utils import (
    factorial,
    find_max,
    gcd,
    is_palindrome,
    is_prime,
    power,
    reverse_string,
)


def main() -> None:
    """Run all function-based problems."""
    # Problem 1-2: Primality check
    n: int = int(input())
    print(is_prime(n))

    # Problem 3: Factorial
    n = int(input())
    print(factorial(n))

    # Problem 4: Find maximum in a list
    nums: list[int] = list(map(int, input().split()))
    print(find_max(nums))

    # Problem 5: Reverse string
    text: str = input()
    print(reverse_string(text))

    # Problem 6: Palindrome check
    text = input()
    print(is_palindrome(text))

    # Problem 7: Power
    base: int = int(input())
    exp: int = int(input())
    print(power(base, exp))

    # Problem 8: GCD
    a: int = int(input())
    b: int = int(input())
    print(gcd(a, b))


if __name__ == "__main__":
    main()
'''

    v1_utils_medium = """\
def is_prime(n):
    if n < 2: return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0: return False
    return True

def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def find_max(nums):
    m = nums[0]
    for x in nums:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def power(b, e):
    r = 1
    for _ in range(e):
        r *= b
    return r

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
"""

    v1_medium = """\
from hw4_utils import (is_prime, factorial, find_max,
    reverse_string, is_palindrome, power, gcd)

n = int(input())
print(is_prime(n))
n = int(input())
print(factorial(n))
nums = list(map(int, input().split()))
print(find_max(nums))
s = input()
print(reverse_string(s))
s = input()
print(is_palindrome(s))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    v1_utils_low = """\
def is_prime(n):
    # Bug: starts from 3, misses check for n=2
    if n < 2: return False
    for i in range(3, n):
        if n % i == 0: return False
    return True

def factorial(n):
    # Bug: returns 0 for n=0 or n=1 because range(2,1) is empty
    # and result starts at 0
    result = 0
    for i in range(2, n + 1):
        result *= i
    return result

def find_max(nums):
    # Bug: compares against 0 instead of first element
    m = 0
    for x in nums:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def power(b, e):
    r = 1
    for _ in range(e):
        r *= b
    return r

def gcd(a, b):
    while b:
        a, b = b, a % b
    return a
"""

    v1_low = """\
from hw4_utils import (is_prime, factorial, find_max,
    reverse_string, is_palindrome, power, gcd)

n = int(input())
print(is_prime(n))
n = int(input())
print(factorial(n))
nums = list(map(int, input().split()))
print(find_max(nums))
s = input()
print(reverse_string(s))
s = input()
print(is_palindrome(s))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    # ── Variation 2: Different algorithm choices ──
    v2_utils_high = '''\
"""HW4 Utilities: Mathematical and string helper functions.

Provides reusable functions for prime checking, factorial computation,
list operations, string manipulation, and number theory.
"""

import math


def is_prime(n: int) -> bool:
    """Test primality using trial division up to sqrt(n).

    Args:
        n: Integer to test.

    Returns:
        True if n is prime.
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i: int = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def factorial(n: int) -> int:
    """Compute factorial iteratively.

    Args:
        n: Non-negative integer.

    Returns:
        n! (n factorial).
    """
    return math.prod(range(1, n + 1)) if n > 0 else 1


def find_max(numbers: list[int]) -> int:
    """Return the maximum element from a list.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        The maximum value.
    """
    maximum: int = numbers[0]
    for num in numbers[1:]:
        if num > maximum:
            maximum = num
    return maximum


def reverse_string(s: str) -> str:
    """Reverse a string using slicing.

    Args:
        s: Input string.

    Returns:
        Reversed string.
    """
    return s[::-1]


def is_palindrome(s: str) -> bool:
    """Check whether a string reads the same forwards and backwards.

    Args:
        s: Input string.

    Returns:
        True if s is a palindrome.
    """
    return s == s[::-1]


def power(base: int, exp: int) -> int:
    """Compute base^exp iteratively.

    Args:
        base: Base integer.
        exp: Non-negative exponent.

    Returns:
        base raised to the power of exp.
    """
    result: int = 1
    for _ in range(exp):
        result *= base
    return result


def gcd(a: int, b: int) -> int:
    """Greatest common divisor via Euclid's algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.

    Returns:
        GCD(a, b).
    """
    while b:
        a, b = b, a % b
    return a
'''

    v2_high = '''\
"""HW4 Solution: Functions and Modular Design.

Driver module that imports utilities from hw4_utils and
processes input for each problem.
"""

from hw4_utils import (
    factorial,
    find_max,
    gcd,
    is_palindrome,
    is_prime,
    power,
    reverse_string,
)


def main() -> None:
    """Process all function problems."""
    # Primality test
    print(is_prime(int(input())))

    # Factorial
    print(factorial(int(input())))

    # Find max in list
    numbers: list[int] = list(map(int, input().split()))
    print(find_max(numbers))

    # Reverse string
    print(reverse_string(input()))

    # Palindrome check
    print(is_palindrome(input()))

    # Power
    b: int = int(input())
    e: int = int(input())
    print(power(b, e))

    # GCD
    x: int = int(input())
    y: int = int(input())
    print(gcd(x, y))


if __name__ == "__main__":
    main()
'''

    v2_utils_medium = """\
def is_prime(n):
    if n < 2: return False
    if n < 4: return True
    if n % 2 == 0: return False
    i = 3
    while i * i <= n:
        if n % i == 0: return False
        i += 2
    return True

def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r

def find_max(lst):
    m = lst[0]
    for x in lst[1:]:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def power(base, exp):
    r = 1
    for _ in range(exp): r *= base
    return r

def gcd(a, b):
    while b: a, b = b, a % b
    return a
"""

    v2_medium = """\
from hw4_utils import *

print(is_prime(int(input())))
print(factorial(int(input())))
nums = list(map(int, input().split()))
print(find_max(nums))
print(reverse_string(input()))
print(is_palindrome(input()))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    v2_utils_low = """\
def is_prime(n):
    if n < 2: return False
    # Bug: checks up to n instead of sqrt(n), but also
    # misses that 2 is prime due to range(2, 2) being empty... wait
    # Actually range(2, n) works for n=2 since it returns empty -> True
    # But: no check for even numbers, very slow for large n
    for i in range(2, n):
        if n % i == 0: return False
    return True

def factorial(n):
    r = 1
    for i in range(1, n + 1):
        r *= i
    return r

def find_max(lst):
    # Bug: returns first element if list has negatives and starts at 0
    m = 0
    for x in lst:
        if x > m: m = x
    return m

def reverse_string(s):
    return s[::-1]

def is_palindrome(s):
    return s == s[::-1]

def power(base, exp):
    r = 1
    for _ in range(exp): r *= base
    return r

def gcd(a, b):
    while b: a, b = b, a % b
    return a
"""

    v2_low = """\
from hw4_utils import *

print(is_prime(int(input())))
print(factorial(int(input())))
nums = list(map(int, input().split()))
print(find_max(nums))
print(reverse_string(input()))
print(is_palindrome(input()))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    # ── Variation 3: Recursive approach where possible ──
    v3_utils_high = '''\
"""HW4 Utility Functions: Recursive and iterative implementations.

Provides helper functions for prime checking, factorial, list
operations, string manipulation, and GCD computation.
"""


def is_prime(n: int) -> bool:
    """Check if n is prime using trial division.

    Args:
        n: The integer to check.

    Returns:
        True if n is a prime number.
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True


def factorial(n: int) -> int:
    """Compute n! recursively.

    Args:
        n: Non-negative integer.

    Returns:
        n factorial.
    """
    if n <= 1:
        return 1
    return n * factorial(n - 1)


def find_max(numbers: list[int]) -> int:
    """Find the largest element in a list.

    Args:
        numbers: Non-empty list of integers.

    Returns:
        Maximum value in the list.
    """
    max_value: int = numbers[0]
    for num in numbers:
        if num > max_value:
            max_value = num
    return max_value


def reverse_string(text: str) -> str:
    """Reverse a string using slicing.

    Args:
        text: String to reverse.

    Returns:
        The reversed string.
    """
    return text[::-1]


def is_palindrome(text: str) -> bool:
    """Check if a string is a palindrome.

    Args:
        text: String to check.

    Returns:
        True if text is a palindrome.
    """
    return text == text[::-1]


def power(base: int, exponent: int) -> int:
    """Compute base^exponent recursively.

    Args:
        base: Base number.
        exponent: Non-negative exponent.

    Returns:
        base raised to the exponent.
    """
    if exponent == 0:
        return 1
    return base * power(base, exponent - 1)


def gcd(a: int, b: int) -> int:
    """Compute GCD using recursive Euclidean algorithm.

    Args:
        a: First positive integer.
        b: Second positive integer.

    Returns:
        Greatest common divisor.
    """
    if b == 0:
        return a
    return gcd(b, a % b)
'''

    v3_high = '''\
"""HW4 Solution: Functions and Modular Design.

Main driver using recursive utility functions from hw4_utils.
"""

from hw4_utils import (
    factorial,
    find_max,
    gcd,
    is_palindrome,
    is_prime,
    power,
    reverse_string,
)


def main() -> None:
    """Execute all function problems."""
    print(is_prime(int(input())))
    print(factorial(int(input())))
    print(find_max(list(map(int, input().split()))))
    print(reverse_string(input()))
    print(is_palindrome(input()))
    base: int = int(input())
    exp: int = int(input())
    print(power(base, exp))
    a: int = int(input())
    b: int = int(input())
    print(gcd(a, b))


if __name__ == "__main__":
    main()
'''

    v3_utils_medium = """\
def is_prime(n):
    if n < 2: return False
    if n == 2: return True
    if n % 2 == 0: return False
    for i in range(3, int(n**0.5) + 1, 2):
        if n % i == 0: return False
    return True

def factorial(n):
    if n <= 1: return 1
    return n * factorial(n - 1)

def find_max(nums):
    m = nums[0]
    for x in nums:
        if x > m: m = x
    return m

def reverse_string(s): return s[::-1]
def is_palindrome(s): return s == s[::-1]

def power(b, e):
    if e == 0: return 1
    return b * power(b, e - 1)

def gcd(a, b):
    if b == 0: return a
    return gcd(b, a % b)
"""

    v3_medium = """\
from hw4_utils import *

print(is_prime(int(input())))
print(factorial(int(input())))
print(find_max(list(map(int, input().split()))))
print(reverse_string(input()))
print(is_palindrome(input()))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    v3_utils_low = """\
def is_prime(n):
    if n < 2: return False
    # Bug: only checks divisibility by 2
    if n % 2 == 0: return False
    return True

def factorial(n):
    if n <= 1: return 1
    return n * factorial(n - 1)

def find_max(nums):
    m = nums[0]
    for x in nums:
        if x > m: m = x
    return m

def reverse_string(s): return s[::-1]
def is_palindrome(s): return s == s[::-1]

def power(b, e):
    if e == 0: return 1
    return b * power(b, e - 1)

def gcd(a, b):
    # Bug: wrong order of arguments in recursive call
    if b == 0: return a
    return gcd(a % b, b)
"""

    v3_low = """\
from hw4_utils import *

print(is_prime(int(input())))
print(factorial(int(input())))
print(find_max(list(map(int, input().split()))))
print(reverse_string(input()))
print(is_palindrome(input()))
b = int(input())
e = int(input())
print(power(b, e))
a = int(input())
b = int(input())
print(gcd(a, b))
"""

    return (
        CodeTemplate(
            template_id="HW4_V1",
            assignment_id="HW4",
            high_quality=v1_high,
            medium_quality=v1_medium,
            low_quality=v1_low,
            utils_high=v1_utils_high,
            utils_medium=v1_utils_medium,
            utils_low=v1_utils_low,
        ),
        CodeTemplate(
            template_id="HW4_V2",
            assignment_id="HW4",
            high_quality=v2_high,
            medium_quality=v2_medium,
            low_quality=v2_low,
            utils_high=v2_utils_high,
            utils_medium=v2_utils_medium,
            utils_low=v2_utils_low,
        ),
        CodeTemplate(
            template_id="HW4_V3",
            assignment_id="HW4",
            high_quality=v3_high,
            medium_quality=v3_medium,
            low_quality=v3_low,
            utils_high=v3_utils_high,
            utils_medium=v3_utils_medium,
            utils_low=v3_utils_low,
        ),
    )


# ── HW5 Templates: Lists and Data Structures ────────────────────────
# Problems (from test cases in assignments.py):
#   TC01: Average of [10, 20, 30] -> 20.0
#   TC02: Remove duplicates [1,2,2,3] -> [1,2,3]
#   TC03: Sort [5,3,1,4,2] -> [1,2,3,4,5]
#   TC04: Second largest [3,1,4,1,5] -> 4
#   TC05: Count occurrences of 3 in [1,3,3,3,2] -> 3
#   TC06: Merge sorted [1,3,5] + [2,4,6] -> [1,2,3,4,5,6]
#   TC07: Squares of 1..4 -> [1,4,9,16]
#   TC08: Flatten [[1,2],[3,4]] -> [1,2,3,4]
# Files: hw5_solution.py + hw5_utils.py


def _build_hw5_templates() -> tuple[CodeTemplate, ...]:
    """Build 3 code template variations for HW5 (Lists, Data Structures).

    Each variation splits logic between hw5_solution.py (main driver)
    and hw5_utils.py (list utility functions). Variations differ in
    use of built-ins vs manual implementation, list comprehensions
    vs explicit loops, and code organization style.

    Used by: module-level _TEMPLATES dict initialization.

    Returns:
        Tuple of 3 CodeTemplate instances for HW5 (with utils files).
    """
    # ── Variation 1: Clean built-in approach ──
    v1_utils_high = '''\
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
'''

    v1_high = '''\
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
'''

    v1_utils_medium = """\
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
"""

    v1_medium = """\
from hw5_utils import *

nums = list(map(int, input().split()))
print(compute_average(nums))
nums = list(map(int, input().split()))
print(" ".join(map(str, remove_duplicates(nums))))
nums = list(map(int, input().split()))
print(" ".join(map(str, sort_list(nums))))
nums = list(map(int, input().split()))
print(second_largest(nums))
target = int(input())
nums = list(map(int, input().split()))
print(count_occurrences(target, nums))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_sorted(a, b))))
n = int(input())
print(" ".join(map(str, generate_squares(n))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten([r1, r2]))))
"""

    v1_utils_low = """\
def compute_average(nums):
    # Bug: integer division
    return sum(nums) // len(nums)

def remove_duplicates(lst):
    # Bug: set() doesn't preserve order
    return list(set(lst))

def sort_list(lst):
    return sorted(lst)

def second_largest(nums):
    # Bug: doesn't handle duplicates properly
    nums_sorted = sorted(nums, reverse=True)
    return nums_sorted[1]

def count_occurrences(target, lst):
    return lst.count(target)

def merge_sorted(a, b):
    # Bug: just concatenates and sorts (not merge algorithm)
    return sorted(a + b)

def generate_squares(n):
    return [i**2 for i in range(1, n + 1)]

def flatten(nested):
    result = []
    for sub in nested:
        result.extend(sub)
    return result
"""

    v1_low = """\
from hw5_utils import *

nums = list(map(int, input().split()))
print(compute_average(nums))
nums = list(map(int, input().split()))
print(" ".join(map(str, remove_duplicates(nums))))
nums = list(map(int, input().split()))
print(" ".join(map(str, sort_list(nums))))
nums = list(map(int, input().split()))
print(second_largest(nums))
target = int(input())
nums = list(map(int, input().split()))
print(count_occurrences(target, nums))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_sorted(a, b))))
n = int(input())
print(" ".join(map(str, generate_squares(n))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten([r1, r2]))))
"""

    # ── Variation 2: List comprehension heavy approach ──
    v2_utils_high = '''\
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
'''

    v2_high = '''\
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
'''

    v2_utils_medium = """\
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
"""

    v2_medium = """\
from hw5_utils import *

print(average(list(map(int, input().split()))))
print(" ".join(map(str, deduplicate(list(map(int, input().split()))))))
print(" ".join(map(str, sort_ascending(list(map(int, input().split()))))))
print(find_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_value(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_two_sorted(a, b))))
print(" ".join(map(str, squares_up_to(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_2d([r1, r2]))))
"""

    v2_utils_low = """\
def average(nums):
    # Bug: integer division
    return sum(nums) // len(nums)

def deduplicate(lst):
    # Bug: uses set() which doesn't preserve order
    return list(set(lst))

def sort_ascending(lst):
    return sorted(lst)

def find_second_largest(nums):
    s = sorted(nums, reverse=True)
    return s[1]

def count_value(target, lst):
    c = 0
    for x in lst:
        if x == target: c += 1
    return c

def merge_two_sorted(a, b):
    return sorted(a + b)

def squares_up_to(n):
    return [x**2 for x in range(1, n + 1)]

def flatten_2d(m):
    return [x for row in m for x in row]
"""

    v2_low = """\
from hw5_utils import *

print(average(list(map(int, input().split()))))
print(" ".join(map(str, deduplicate(list(map(int, input().split()))))))
print(" ".join(map(str, sort_ascending(list(map(int, input().split()))))))
print(find_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_value(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_two_sorted(a, b))))
print(" ".join(map(str, squares_up_to(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_2d([r1, r2]))))
"""

    # ── Variation 3: Manual implementation approach ──
    v3_utils_high = '''\
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
'''

    v3_high = '''\
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
'''

    v3_utils_medium = """\
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
"""

    v3_medium = """\
from hw5_utils import *

print(calc_average(list(map(int, input().split()))))
print(" ".join(map(str, unique_elements(list(map(int, input().split()))))))
print(" ".join(map(str, bubble_sort(list(map(int, input().split()))))))
print(get_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_element(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_lists(a, b))))
print(" ".join(map(str, make_squares(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_lists([r1, r2]))))
"""

    v3_utils_low = """\
def calc_average(nums):
    # Bug: integer division
    total = 0
    for n in nums: total += n
    return total // len(nums)

def unique_elements(lst):
    # Bug: set doesn't preserve order
    return list(set(lst))

def bubble_sort(lst):
    arr = lst.copy()
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def get_second_largest(nums):
    # Bug: doesn't handle duplicates
    nums_s = sorted(nums, reverse=True)
    return nums_s[1]

def count_element(target, lst):
    c = 0
    for x in lst:
        if x == target: c += 1
    return c

def merge_lists(a, b):
    return sorted(a + b)

def make_squares(n):
    return [i*i for i in range(1, n+1)]

def flatten_lists(nested):
    res = []
    for sub in nested:
        for x in sub: res.append(x)
    return res
"""

    v3_low = """\
from hw5_utils import *

print(calc_average(list(map(int, input().split()))))
print(" ".join(map(str, unique_elements(list(map(int, input().split()))))))
print(" ".join(map(str, bubble_sort(list(map(int, input().split()))))))
print(get_second_largest(list(map(int, input().split()))))
t = int(input())
print(count_element(t, list(map(int, input().split()))))
a = list(map(int, input().split()))
b = list(map(int, input().split()))
print(" ".join(map(str, merge_lists(a, b))))
print(" ".join(map(str, make_squares(int(input())))))
r1 = list(map(int, input().split()))
r2 = list(map(int, input().split()))
print(" ".join(map(str, flatten_lists([r1, r2]))))
"""

    return (
        CodeTemplate(
            template_id="HW5_V1",
            assignment_id="HW5",
            high_quality=v1_high,
            medium_quality=v1_medium,
            low_quality=v1_low,
            utils_high=v1_utils_high,
            utils_medium=v1_utils_medium,
            utils_low=v1_utils_low,
        ),
        CodeTemplate(
            template_id="HW5_V2",
            assignment_id="HW5",
            high_quality=v2_high,
            medium_quality=v2_medium,
            low_quality=v2_low,
            utils_high=v2_utils_high,
            utils_medium=v2_utils_medium,
            utils_low=v2_utils_low,
        ),
        CodeTemplate(
            template_id="HW5_V3",
            assignment_id="HW5",
            high_quality=v3_high,
            medium_quality=v3_medium,
            low_quality=v3_low,
            utils_high=v3_utils_high,
            utils_medium=v3_utils_medium,
            utils_low=v3_utils_low,
        ),
    )


# ── Template Registry ────────────────────────────────────────────────
# Module-level mapping from assignment_id to available code templates.
# Populated once at import time by the _build_hw*_templates() functions.
# This follows the same pattern as _TEST_CASES in assignments.py.
# Used by: _select_template() to randomly pick a template variation.

_TEMPLATES: dict[str, tuple[CodeTemplate, ...]] = {
    "HW1": _build_hw1_templates(),
    "HW2": _build_hw2_templates(),
    "HW3": _build_hw3_templates(),
    "HW4": _build_hw4_templates(),
    "HW5": _build_hw5_templates(),
}


# ── Public API ───────────────────────────────────────────────────────


def generate_code_files(
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    rng: random.Random,
) -> list[GeneratedCodeFile]:
    """Generate Python source code files for a single submission attempt.

    This is the main entry point for code generation. It produces 1-2
    GeneratedCodeFile instances depending on the assignment's
    required_files (1 file for HW1-HW3, 2 files for HW4-HW5).

    Code quality varies based on the student's skill_level, adjusted
    by attempt number (later attempts produce better code).

    The generation process:
        1. Compute effective_skill from skill_level and attempt_no.
        2. Select a quality tier (high/medium/low) based on effective_skill.
        3. Choose a random template variation for this assignment.
        4. Extract the appropriate quality variant from the template.
        5. Apply randomized style mutations for individuality.
        6. Pad or trim content to meet FILE_SIZE_PYTHON constraints.
        7. Wrap results in GeneratedCodeFile instances.

    Used by: generate_data.py (Step 10, main loop calls this for each
             student-assignment-attempt triple),
             submission_builder.py (Step 5, receives the returned files)

    Args:
        student:    The student profile (provides skill_level).
        assignment: The assignment definition (provides assignment_id,
                    required_files).
        attempt_no: Which attempt this is (1, 2, or 3). Higher attempts
                    boost effective skill via ATTEMPT_SKILL_BOOST.
        rng:        Seeded Random instance for reproducible generation.
                    Must be created via config.create_rng().

    Returns:
        A list of GeneratedCodeFile instances. Length matches
        len(assignment.required_files): 1 for HW1-HW3, 2 for HW4-HW5.

    Raises:
        ValueError: If assignment.assignment_id is not recognized
                    (not in HW1-HW5).
    """
    # Step 1: Compute effective skill adjusted by attempt number.
    effective_skill: float = _compute_effective_skill(student.skill_level, attempt_no)

    # Step 2: Select quality tier (high / medium / low).
    tier: str = _select_quality_tier(effective_skill)

    # Step 3: Randomly select a template variation for this assignment.
    template: CodeTemplate = _select_template(assignment.assignment_id, rng)

    # Step 4: Extract the appropriate quality variant.
    if tier == "high":
        solution_content = template.high_quality
        utils_content = template.utils_high
    elif tier == "medium":
        solution_content = template.medium_quality
        utils_content = template.utils_medium
    else:
        solution_content = template.low_quality
        utils_content = template.utils_low

    min_bytes: int = FILE_SIZE_PYTHON[0]
    max_bytes: int = FILE_SIZE_PYTHON[1]

    # Step 5-6: Apply style mutations and pad to size for solution file.
    solution_content = _apply_style_mutations(solution_content, effective_skill, rng)
    solution_content = _pad_to_size(
        solution_content, min_bytes, max_bytes, effective_skill, rng
    )

    # Step 7: Build the solution GeneratedCodeFile.
    result: list[GeneratedCodeFile] = [
        GeneratedCodeFile(
            filename=assignment.required_files[0],
            content=solution_content,
            size_bytes=len(solution_content.encode("utf-8")),
        )
    ]

    # Step 8: If utils file exists (HW4, HW5), process it too.
    if utils_content is not None and len(assignment.required_files) > 1:
        utils_content = _apply_style_mutations(utils_content, effective_skill, rng)
        utils_content = _pad_to_size(
            utils_content, min_bytes, max_bytes, effective_skill, rng
        )
        result.append(
            GeneratedCodeFile(
                filename=assignment.required_files[1],
                content=utils_content,
                size_bytes=len(utils_content.encode("utf-8")),
            )
        )

    return result
