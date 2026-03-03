"""Plagiarism and similarity simulation for the seed data pipeline.

This module simulates plagiarism detection by creating pairwise submission
comparisons, generating similarity scores, and tagging submissions as
plagiarism suspects or corrupted.  No actual student code is executed;
instead, AST-level transformations (variable renaming, dead code insertion)
are applied to real generated code to produce realistically similar pairs.

The single public entry point is :func:`generate_plagiarism_pairs`, which
returns a ``PlagiarismResult`` frozen dataclass containing SimilarityScore
records, SubmissionTag records, corrupted submission IDs, and the list of
plagiarism pair mappings.

Key exports:
    PlagiarismResult          -- Frozen dataclass holding all outputs.
    generate_plagiarism_pairs -- Main entry point.

Module dependency graph (imports from):
    config.py              -> SimilarityMethod, TagType, TagSource, create_rng
    models.py              -> SimilarityScore, SubmissionTag
    submission_builder.py  -> SubmissionBundle
    code_generator.py      -> GeneratedCodeFile (accessed via SubmissionBundle)

Consumed by:
    generate_data.py  (Step 10 -- calls generate_plagiarism_pairs() once
                       after all bundles are assembled, writes results to
                       metadata/similarity_scores.csv and metadata/tags.csv)
"""

from __future__ import annotations

import ast
import random
import re
import uuid
from collections import defaultdict
from dataclasses import dataclass

from rapidfuzz import fuzz

from make_simul_data.seed_data.config import (
    SimilarityMethod,
    TagSource,
    TagType,
)
from make_simul_data.seed_data.models import (
    SimilarityScore,
    SubmissionTag,
)
from make_simul_data.seed_data.submission_builder import SubmissionBundle

# ── Plagiarism Rate Constants ────────────────────────────────────────────

# Fraction of submissions selected for plagiarism pairing.
# Approximately 10% of total submissions will be flagged as plagiarism
# suspects.  This rate is applied per-assignment to ensure a realistic
# distribution across the entire course.
# Used by: _select_plagiarism_pairs()
PLAGIARISM_RATE: float = 0.10

# Fraction of submissions marked as corrupted (broken ZIP, encoding
# errors, or oversized binary data).  About 3% of all submissions
# simulate data corruption that students might encounter when uploading
# files.
# Used by: _select_corrupted_submissions()
CORRUPTION_RATE: float = 0.03

# Similarity percentage threshold at or above which a comparison pair
# is flagged for manual review.  Scores >= this value set flagged=True
# on the corresponding SimilarityScore records.
# Used by: generate_plagiarism_pairs() (when creating SimilarityScore)
PLAGIARISM_THRESHOLD: float = 80.0

# Number of non-flagged background comparison pairs to generate per
# assignment.  These provide a realistic baseline of low-similarity
# comparisons alongside the intentionally high-similarity plagiarism
# pairs, helping downstream analytics distinguish real plagiarism.
# Used by: _generate_background_scores()
BACKGROUND_PAIRS_PER_ASSIGNMENT: int = 10

# Confidence range for PLAGIARISM_SUSPECT tags.
# Simulates realistic confidence variation in automated detection.
# Used by: _generate_plagiarism_tags()
_PLAGIARISM_CONFIDENCE_MIN: float = 0.85
_PLAGIARISM_CONFIDENCE_MAX: float = 0.99

# Confidence range for CORRUPTED tags.
# Used by: _generate_corruption_tags()
_CORRUPTION_CONFIDENCE_MIN: float = 0.70
_CORRUPTION_CONFIDENCE_MAX: float = 1.00

# ── Python Builtins (Do NOT Rename) ──────────────────────────────────────

# Frozenset of Python builtin names that must never be renamed by the
# VariableRenamer AST transformer.  Renaming any of these would produce
# code that fails to execute, defeating the purpose of the simulation.
# Used by: VariableRenamer._get_renamed()
_PYTHON_BUILTINS: frozenset[str] = frozenset(
    {
        "print",
        "input",
        "range",
        "len",
        "int",
        "str",
        "float",
        "list",
        "dict",
        "set",
        "tuple",
        "bool",
        "type",
        "sorted",
        "enumerate",
        "zip",
        "map",
        "filter",
        "sum",
        "min",
        "max",
        "abs",
        "round",
        "open",
        "True",
        "False",
        "None",
        "isinstance",
        "super",
        "object",
        "Exception",
        "ValueError",
        "TypeError",
        "KeyError",
        "IndexError",
        "__name__",
        "__main__",
    }
)

# ── Variable Renaming Pools ──────────────────────────────────────────────

# Suffix pool appended to variable names when no synonym exists.
# Simulates a plagiarizer who systematically adds suffixes to identifiers.
# Used by: VariableRenamer._get_renamed()
_RENAME_SUFFIXES: tuple[str, ...] = (
    "_v2",
    "_new",
    "_val",
    "_data",
    "_temp",
    "_result",
    "_out",
    "_var",
    "_num",
    "_x",
    "2",
    "_mod",
    "_copy",
)

# Synonym mapping for common CS1 variable names.
# When a variable name appears in this dict, its replacement is chosen
# from the associated tuple instead of appending a suffix.  This produces
# more natural-looking plagiarized code.
# Used by: VariableRenamer._get_renamed()
_RENAME_SYNONYMS: dict[str, tuple[str, ...]] = {
    "result": ("output", "answer", "res", "ret"),
    "total": ("sum_val", "accumulator", "tally"),
    "count": ("cnt", "num_items", "counter"),
    "data": ("values", "items", "info", "numbers"),
    "temp": ("tmp", "holder", "swap_val"),
    "i": ("j", "k", "idx", "index"),
    "j": ("k", "idx", "jj"),
    "x": ("y", "val", "num"),
    "n": ("size", "length", "num"),
    "num": ("number", "value", "n"),
    "lst": ("arr", "my_list", "collection"),
    "arr": ("lst", "my_list", "collection"),
    "s": ("text", "line", "word"),
    "msg": ("message", "text", "output"),
    "grade": ("score", "mark", "points"),
    "average": ("avg", "mean", "avg_val"),
}

# ── Dead Code Templates ──────────────────────────────────────────────────

# Templates for dead (unused) variable assignments inserted between
# existing statements.  Each string is a valid Python statement that
# can be parsed by ast.parse() and has no side effects.
# Used by: DeadCodeInserter._inject_dead_code()
_DEAD_CODE_TEMPLATES: tuple[str, ...] = (
    "_unused_var = 0",
    "_debug_flag = False",
    "_temp_storage = []",
    "_ = None",
    "_placeholder = 'TODO: remove this'",
    "_counter = 0",
    "_check = True",
    "_buffer = ''",
)

# Templates for dead (unused) function definitions appended to module
# or function bodies.  These simulate a plagiarizer who adds decoy
# functions to disguise copied code structure.
# Used by: DeadCodeInserter._inject_dead_code()
_DEAD_FUNCTION_TEMPLATES: tuple[str, ...] = (
    "def _helper():\n    pass",
    "def _debug_print(x):\n    pass",
    "def _unused_check(val):\n    return True",
)

# ── Extra Comment Pool ───────────────────────────────────────────────────

# Comments injected during _reformat_code() to obfuscate similarity.
# Simulates a plagiarizer who adds their own comments to make copied
# code look original.
# Used by: _reformat_code()
_EXTRA_COMMENTS: tuple[str, ...] = (
    "# this is my solution",
    "# I worked on this for a while",
    "# check this later",
    "# seems to work correctly",
    "# based on the lecture notes",
    "# I tested this with several inputs",
    "# should handle edge cases",
    "# my approach to the problem",
    "# rewritten from scratch",
    "# debugging done",
)


# ── Return Type ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PlagiarismResult:
    """Immutable container for all plagiarism simulation outputs.

    Bundles every artifact produced by the plagiarism simulation step
    into a single return value, following the same pattern as
    GradingOutcome in grading_engine.py.

    Created by: generate_plagiarism_pairs() in this module.
    Consumed by: generate_data.py (Step 10 -- writes fields to CSV metadata
                 files: similarity_scores.csv and submission_tags.csv).

    Attributes:
        similarity_scores: Tuple of SimilarityScore Pydantic model instances.
                           Contains both flagged (plagiarism) and unflagged
                           (background) pairwise comparisons.  Each record
                           specifies the comparison method, similarity
                           percentage, and flagged boolean.
        tags:              Tuple of SubmissionTag records for both
                           PLAGIARISM_SUSPECT and CORRUPTED submissions.
                           These supplement the tags already created by
                           grading_engine.py.
        corrupted_ids:     Tuple of submission UUIDs whose files should be
                           considered corrupted.  Downstream modules can use
                           these IDs to apply file-level corruption.
        plagiarism_pairs:  Tuple of (source_id, target_id) UUID pairs that
                           represent which submissions were identified as
                           plagiarism clones of each other.
    """

    similarity_scores: tuple[SimilarityScore, ...]
    tags: tuple[SubmissionTag, ...]
    corrupted_ids: tuple[uuid.UUID, ...]
    plagiarism_pairs: tuple[tuple[uuid.UUID, uuid.UUID], ...]


# ── AST Transformation: Variable Renamer ─────────────────────────────────


class VariableRenamer(ast.NodeTransformer):
    """AST node transformer that renames user-defined variables and functions.

    Simulates a plagiarizer who copies code and systematically renames
    identifiers to disguise the origin.  Python builtins (print, input,
    range, etc.) are preserved to keep the transformed code executable.

    The renaming is *consistent*: every occurrence of a given identifier
    receives the same replacement, maintaining semantic correctness.

    Created by: _transform_code() in this module.
    Used by: generate_plagiarism_pairs() (applied to source code of
             selected plagiarism pairs).

    Attributes:
        _rng:     Seeded Random instance for deterministic renaming.
        _mapping: Internal dict mapping original names to their renamed
                  versions, ensuring consistency across all occurrences.
    """

    def __init__(self, rng: random.Random) -> None:
        """Initialize the renamer with a seeded random generator.

        Args:
            rng: Seeded Random instance from config.create_rng().
        """
        super().__init__()
        self._rng = rng
        self._mapping: dict[str, str] = {}

    def _get_renamed(self, name: str) -> str:
        """Get or create a renamed version of the given identifier.

        If the name is a Python builtin, it is returned unchanged.
        If the name already has a mapping, the existing rename is reused
        for consistency.  Otherwise, a new rename is generated using
        either a synonym lookup or a suffix append.

        Args:
            name: The original identifier string.

        Returns:
            The renamed identifier (may be identical if builtin).
        """
        if name in _PYTHON_BUILTINS:
            return name
        if name in self._mapping:
            return self._mapping[name]
        # Try synonym first, then fall back to suffix.
        if name in _RENAME_SYNONYMS:
            new_name = self._rng.choice(_RENAME_SYNONYMS[name])
        else:
            suffix = self._rng.choice(_RENAME_SUFFIXES)
            new_name = f"{name}{suffix}"
        self._mapping[name] = new_name
        return new_name

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Rename function name and its argument names.

        Args:
            node: The FunctionDef AST node to transform.

        Returns:
            The transformed FunctionDef with renamed identifiers.
        """
        node.name = self._get_renamed(node.name)
        for arg in node.args.args:
            arg.arg = self._get_renamed(arg.arg)
        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Rename variable references in Name nodes.

        Args:
            node: The Name AST node to transform.

        Returns:
            The transformed Name node with the renamed identifier.
        """
        node.id = self._get_renamed(node.id)
        return node


# ── AST Transformation: Dead Code Inserter ───────────────────────────────


class DeadCodeInserter(ast.NodeTransformer):
    """AST node transformer that inserts semantically irrelevant code.

    Simulates a plagiarizer who adds unused variables, no-op functions,
    and redundant statements to obfuscate copied code structure.  The
    insertion density is controlled by a probability parameter.

    Created by: _transform_code() in this module.
    Used by: generate_plagiarism_pairs() (applied after VariableRenamer).

    Attributes:
        _rng:     Seeded Random instance for deterministic insertion.
        _density: Probability (0.0-1.0) of inserting dead code at each
                  gap between existing statements.  Default: 0.3.
    """

    def __init__(self, rng: random.Random, density: float = 0.3) -> None:
        """Initialize the inserter with a seeded RNG and density.

        Args:
            rng:     Seeded Random instance from config.create_rng().
            density: Probability of inserting dead code at each position.
        """
        super().__init__()
        self._rng = rng
        self._density = density

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Insert dead code into the module's top-level body.

        Args:
            node: The Module AST node.

        Returns:
            The Module with dead code injected between statements.
        """
        node.body = self._inject_dead_code(node.body, allow_functions=True)
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Insert dead code (variable assignments only) into function bodies.

        Only inserts simple variable-style dead code inside function
        bodies to avoid deeply nested decoy functions that could cause
        infinite recursion during AST traversal.

        Args:
            node: The FunctionDef AST node.

        Returns:
            The FunctionDef with dead code injected into its body.
        """
        node.body = self._inject_dead_code(node.body, allow_functions=False)
        return node

    def _inject_dead_code(
        self,
        body: list[ast.stmt],
        *,
        allow_functions: bool = False,
    ) -> list[ast.stmt]:
        """Insert dead code statements at random positions in a body.

        Walks through the existing statements and probabilistically
        inserts one dead code template before each statement.  Dead
        function templates are only inserted at the module level
        (allow_functions=True) to prevent infinite recursion when
        the AST visitor processes nested function definitions.

        Args:
            body:            The list of AST statement nodes.
            allow_functions: If True, also insert dead function definitions.
                             Should be True only for module-level bodies.

        Returns:
            A new list with dead code nodes interspersed.
        """
        new_body: list[ast.stmt] = []
        for stmt in body:
            if self._rng.random() < self._density:
                template = self._rng.choice(_DEAD_CODE_TEMPLATES)
                dead_nodes = ast.parse(template).body
                new_body.extend(dead_nodes)
            new_body.append(stmt)
        # Only append dead function definitions at the module level
        # to avoid infinite recursion from visit_FunctionDef re-entering.
        if allow_functions and self._rng.random() < self._density:
            func_template = self._rng.choice(_DEAD_FUNCTION_TEMPLATES)
            dead_func = ast.parse(func_template).body
            new_body.extend(dead_func)
        return new_body


# ── Code Transformation Helpers ──────────────────────────────────────────


def _reformat_code(source: str, rng: random.Random) -> str:
    """Apply cosmetic formatting changes to obfuscate code similarity.

    Modifies whitespace, quote style, and adds comments without changing
    the code's semantics.  These transformations reduce text-based
    similarity while preserving AST-based similarity.

    Used by: _transform_code() in this module.

    Args:
        source: The Python source code string to reformat.
        rng:    Seeded Random instance for deterministic transformations.

    Returns:
        The reformatted source code string.
    """
    lines = source.split("\n")

    # 1. Randomly swap quote style (double <-> single) with 50% chance.
    if rng.random() < 0.5:
        # Replace double-quoted strings with single-quoted.
        new_lines: list[str] = []
        for line in lines:
            # Only replace simple string literals, not docstrings.
            if '"""' not in line and "'''" not in line:
                line = re.sub(r'"([^"\\]*)"', r"'\1'", line)
            new_lines.append(line)
        lines = new_lines
    else:
        # Replace single-quoted strings with double-quoted.
        new_lines = []
        for line in lines:
            if '"""' not in line and "'''" not in line:
                line = re.sub(r"'([^'\\]*)'", r'"\1"', line)
            new_lines.append(line)
        lines = new_lines

    # 2. Insert 2-5 random comments at random positions.
    n_comments = rng.randint(2, 5)
    for _ in range(n_comments):
        comment = rng.choice(_EXTRA_COMMENTS)
        # Insert after a random existing line (not at position 0).
        if len(lines) > 1:
            pos = rng.randint(1, len(lines) - 1)
            # Match indentation of the preceding line to avoid
            # misaligned comments when the target line is empty.
            ref_line = lines[pos - 1]
            indent = len(ref_line) - len(ref_line.lstrip())
            lines.insert(pos, " " * indent + comment)

    # 3. Add or remove blank lines between top-level statements.
    final_lines: list[str] = []
    for line in lines:
        final_lines.append(line)
        # Add extra blank line after function/class definitions sometimes.
        stripped = line.strip()
        if stripped.startswith(("def ", "class ")) and rng.random() < 0.3:
            final_lines.append("")

    return "\n".join(final_lines)


def _transform_code(source: str, rng: random.Random) -> str:
    """Apply all AST transformations and reformatting to source code.

    Orchestrates the full plagiarism transformation pipeline:
    1. Parse source into AST.
    2. Apply VariableRenamer to rename identifiers.
    3. Apply DeadCodeInserter to add obfuscation code.
    4. Unparse back to source string.
    5. Apply cosmetic reformatting.

    If AST parsing fails (e.g., low-quality code with syntax errors),
    falls back to cosmetic reformatting only.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        source: The original Python source code string.
        rng:    Seeded Random instance for deterministic transformations.

    Returns:
        The transformed source code string.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        # Fallback: apply only cosmetic changes for unparseable code.
        return _reformat_code(source, rng)

    # Apply AST transformations in sequence.
    renamer = VariableRenamer(rng)
    tree = renamer.visit(tree)
    ast.fix_missing_locations(tree)

    inserter = DeadCodeInserter(rng)
    tree = inserter.visit(tree)
    ast.fix_missing_locations(tree)

    try:
        transformed = ast.unparse(tree)
    except (ValueError, RecursionError):
        # ast.unparse() may fail on deeply nested or malformed AST.
        # Fall back to cosmetic-only reformatting of the original source.
        return _reformat_code(source, rng)

    return _reformat_code(transformed, rng)


# ── Similarity Computation Functions ─────────────────────────────────────


def _extract_ast_node_sequence(source: str) -> str:
    """Extract a normalized sequence of AST node type names.

    Walks the AST depth-first and concatenates node type names into a
    single space-separated string.  This representation is resistant to
    variable renaming and formatting changes, making it ideal for
    structural similarity comparison.

    Used by: _compute_ast_similarity() in this module.

    Args:
        source: Python source code string.

    Returns:
        Space-separated string of AST node type names.

    Raises:
        SyntaxError: If the source cannot be parsed.
    """
    tree = ast.parse(source)
    node_types: list[str] = []
    for node in ast.walk(tree):
        node_types.append(type(node).__name__)
    return " ".join(node_types)


def _compute_ast_similarity(source_a: str, source_b: str) -> float:
    """Compute structural similarity between two Python source files.

    Extracts AST node type sequences from both sources and compares
    them using rapidfuzz.fuzz.ratio().  This method is resistant to
    variable renaming and formatting changes.

    Falls back to text-based similarity if either source fails to parse.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        source_a: First Python source code string.
        source_b: Second Python source code string.

    Returns:
        Similarity percentage from 0.0 to 100.0.
    """
    try:
        seq_a = _extract_ast_node_sequence(source_a)
        seq_b = _extract_ast_node_sequence(source_b)
    except SyntaxError:
        # Fall back to text similarity if AST parsing fails.
        return _compute_text_similarity(source_a, source_b)
    return fuzz.ratio(seq_a, seq_b)


def _compute_text_similarity(source_a: str, source_b: str) -> float:
    """Compute text-level similarity using edit-distance ratio.

    Uses rapidfuzz.fuzz.ratio() which computes the normalized
    Levenshtein distance ratio between the two strings.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        source_a: First source code string.
        source_b: Second source code string.

    Returns:
        Similarity percentage from 0.0 to 100.0.
    """
    return fuzz.ratio(source_a, source_b)


def _compute_token_similarity(source_a: str, source_b: str) -> float:
    """Compute token-based similarity using order-independent comparison.

    Uses rapidfuzz.fuzz.token_sort_ratio() which tokenizes both strings,
    sorts the tokens, then computes the edit-distance ratio.  This is
    resistant to statement reordering.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        source_a: First source code string.
        source_b: Second source code string.

    Returns:
        Similarity percentage from 0.0 to 100.0.
    """
    return fuzz.token_sort_ratio(source_a, source_b)


# ── Pair Selection ───────────────────────────────────────────────────────


def _select_plagiarism_pairs(
    bundles: list[SubmissionBundle],
    rng: random.Random,
) -> list[tuple[SubmissionBundle, SubmissionBundle]]:
    """Select submission pairs for plagiarism simulation.

    Groups bundles by assignment_id and selects ~PLAGIARISM_RATE/2
    pairs per assignment (since each pair involves 2 submissions).
    Only bundles with at least one code file are eligible.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        bundles: All SubmissionBundle instances from the pipeline.
        rng:     Seeded Random instance for deterministic selection.

    Returns:
        List of (source_bundle, target_bundle) tuples.
    """
    # Group bundles by assignment_id.
    by_assignment: dict[str, list[SubmissionBundle]] = defaultdict(list)
    for bundle in bundles:
        # Only include bundles that have code files for comparison.
        if bundle.code_files:
            aid = bundle.submission.assignment_id
            by_assignment[aid].append(bundle)

    pairs: list[tuple[SubmissionBundle, SubmissionBundle]] = []
    for _aid, group in sorted(by_assignment.items()):
        if len(group) < 2:
            continue
        # Number of pairs: ~PLAGIARISM_RATE / 2 of the group size.
        n_pairs = max(1, round(len(group) * PLAGIARISM_RATE / 2))
        # Need 2 distinct submissions per pair.
        n_needed = min(n_pairs * 2, len(group))
        # Ensure even number for pairing.
        if n_needed % 2 != 0:
            n_needed -= 1
        if n_needed < 2:
            continue
        selected = rng.sample(group, k=n_needed)
        for i in range(0, n_needed, 2):
            pairs.append((selected[i], selected[i + 1]))

    return pairs


# ── Corruption Helpers ───────────────────────────────────────────────────


def _select_corrupted_submissions(
    bundles: list[SubmissionBundle],
    plagiarism_ids: set[uuid.UUID],
    rng: random.Random,
) -> list[uuid.UUID]:
    """Select ~CORRUPTION_RATE of submissions to mark as corrupted.

    Excludes submissions already flagged for plagiarism to avoid
    conflating the two simulation categories.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        bundles:         All SubmissionBundle instances.
        plagiarism_ids:  Set of submission UUIDs already in plagiarism
                         pairs (excluded from corruption selection).
        rng:             Seeded Random instance.

    Returns:
        List of submission UUIDs to mark as corrupted.
    """
    eligible = [b for b in bundles if b.submission.submission_id not in plagiarism_ids]
    n_corrupt = max(1, round(len(eligible) * CORRUPTION_RATE))
    n_corrupt = min(n_corrupt, len(eligible))
    selected = rng.sample(eligible, k=n_corrupt)
    return [b.submission.submission_id for b in selected]


def _generate_corruption_tags(
    corrupted_ids: list[uuid.UUID],
    rng: random.Random,
) -> list[SubmissionTag]:
    """Create CORRUPTED SubmissionTag records for corrupted submissions.

    Each tag has a confidence value in the range
    [_CORRUPTION_CONFIDENCE_MIN, _CORRUPTION_CONFIDENCE_MAX].

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        corrupted_ids: List of submission UUIDs to tag as corrupted.
        rng:           Seeded Random instance.

    Returns:
        List of SubmissionTag Pydantic model instances with tag=CORRUPTED.
    """
    tags: list[SubmissionTag] = []
    for sid in corrupted_ids:
        confidence = rng.uniform(_CORRUPTION_CONFIDENCE_MIN, _CORRUPTION_CONFIDENCE_MAX)
        tags.append(
            SubmissionTag(
                submission_id=sid,
                tag=TagType.CORRUPTED,
                source=TagSource.AUTOMATED,
                confidence=round(confidence, 4),
            )
        )
    return tags


def _generate_plagiarism_tags(
    plagiarism_ids: set[uuid.UUID],
    rng: random.Random,
) -> list[SubmissionTag]:
    """Create PLAGIARISM_SUSPECT SubmissionTag records.

    Each tag has a confidence value in the range
    [_PLAGIARISM_CONFIDENCE_MIN, _PLAGIARISM_CONFIDENCE_MAX].

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        plagiarism_ids: Set of submission UUIDs involved in plagiarism.
        rng:            Seeded Random instance.

    Returns:
        List of SubmissionTag Pydantic model instances with
        tag=PLAGIARISM_SUSPECT.
    """
    tags: list[SubmissionTag] = []
    for sid in sorted(plagiarism_ids, key=str):
        confidence = rng.uniform(_PLAGIARISM_CONFIDENCE_MIN, _PLAGIARISM_CONFIDENCE_MAX)
        tags.append(
            SubmissionTag(
                submission_id=sid,
                tag=TagType.PLAGIARISM_SUSPECT,
                source=TagSource.AUTOMATED,
                confidence=round(confidence, 4),
            )
        )
    return tags


# ── Background Score Generation ──────────────────────────────────────────


def _generate_background_scores(
    bundles: list[SubmissionBundle],
    flagged_pair_ids: set[tuple[uuid.UUID, uuid.UUID]],
    rng: random.Random,
) -> list[SimilarityScore]:
    """Generate low-similarity background comparison scores.

    Creates BACKGROUND_PAIRS_PER_ASSIGNMENT non-flagged SimilarityScore
    records per assignment to provide a realistic baseline of
    low-similarity comparisons alongside plagiarism pairs.

    Used by: generate_plagiarism_pairs() in this module.

    Args:
        bundles:          All SubmissionBundle instances.
        flagged_pair_ids: Set of (source_id, target_id) UUID tuples
                          already flagged as plagiarism (to avoid).
        rng:              Seeded Random instance.

    Returns:
        List of SimilarityScore records with flagged=False.
    """
    # Group bundles by assignment_id.
    by_assignment: dict[str, list[SubmissionBundle]] = defaultdict(list)
    for bundle in bundles:
        if bundle.code_files:
            aid = bundle.submission.assignment_id
            by_assignment[aid].append(bundle)

    scores: list[SimilarityScore] = []
    methods = list(SimilarityMethod)

    for _aid, group in sorted(by_assignment.items()):
        if len(group) < 2:
            continue
        pairs_generated = 0
        attempts = 0
        max_attempts = BACKGROUND_PAIRS_PER_ASSIGNMENT * 5

        while (
            pairs_generated < BACKGROUND_PAIRS_PER_ASSIGNMENT
            and attempts < max_attempts
        ):
            attempts += 1
            pair = rng.sample(group, k=2)
            sid_a = pair[0].submission.submission_id
            sid_b = pair[1].submission.submission_id
            # Skip if this pair is already flagged.
            if (sid_a, sid_b) in flagged_pair_ids or (
                sid_b,
                sid_a,
            ) in flagged_pair_ids:
                continue

            # Compute real similarity between the two code files.
            code_a = pair[0].code_files[0].content
            code_b = pair[1].code_files[0].content
            method = rng.choice(methods)

            if method == SimilarityMethod.AST_BASED:
                sim_pct = _compute_ast_similarity(code_a, code_b)
            elif method == SimilarityMethod.TOKEN_BASED:
                sim_pct = _compute_token_similarity(code_a, code_b)
            else:
                sim_pct = _compute_text_similarity(code_a, code_b)

            # Ensure background scores stay below the threshold.
            sim_pct = min(sim_pct, PLAGIARISM_THRESHOLD - 1.0)

            scores.append(
                SimilarityScore(
                    sim_id=uuid.uuid4(),
                    submission_id=sid_a,
                    compared_to=sid_b,
                    method=method.value,
                    similarity_pct=round(sim_pct, 2),
                    flagged=False,
                )
            )
            pairs_generated += 1

    return scores


# ── Public API ───────────────────────────────────────────────────────────


def generate_plagiarism_pairs(
    bundles: list[SubmissionBundle],
    rng: random.Random,
) -> PlagiarismResult:
    """Generate plagiarism simulation data for a set of submission bundles.

    This is the main public entry point for Step 8.  It performs:

    1. Select ~10% of submissions for plagiarism pairing (per assignment).
    2. For each pair, transform the source code using AST renaming,
       dead code insertion, and cosmetic reformatting.
    3. Compute similarity scores using all three methods (AST-based,
       token-based, text-based) for each plagiarism pair.
    4. Create SimilarityScore records (flagged=True where >= threshold).
    5. Generate PLAGIARISM_SUSPECT tags for involved submissions.
    6. Create background (non-plagiarism) comparison pairs.
    7. Select ~3% of submissions for corruption tagging.
    8. Return PlagiarismResult with all collected data.

    Args:
        bundles: List of SubmissionBundle instances from
                 submission_builder.py.  Must contain at least 2 bundles
                 for any pairing to occur.
        rng:     Seeded Random instance from config.create_rng().

    Returns:
        PlagiarismResult frozen dataclass containing similarity scores,
        tags, corrupted IDs, and plagiarism pair mappings.
    """
    # Handle edge case: too few bundles for any comparison.
    if len(bundles) < 2:
        return PlagiarismResult(
            similarity_scores=(),
            tags=(),
            corrupted_ids=(),
            plagiarism_pairs=(),
        )

    # Step 1: Select plagiarism pairs grouped by assignment.
    pairs = _select_plagiarism_pairs(bundles, rng)

    # Step 2-4: Transform code and compute similarity for each pair.
    all_scores: list[SimilarityScore] = []
    plagiarism_pair_ids: list[tuple[uuid.UUID, uuid.UUID]] = []
    plagiarism_sub_ids: set[uuid.UUID] = set()
    flagged_pair_set: set[tuple[uuid.UUID, uuid.UUID]] = set()

    for source_bundle, target_bundle in pairs:
        source_id = source_bundle.submission.submission_id
        target_id = target_bundle.submission.submission_id
        plagiarism_pair_ids.append((source_id, target_id))
        plagiarism_sub_ids.add(source_id)
        plagiarism_sub_ids.add(target_id)
        flagged_pair_set.add((source_id, target_id))

        # Get source code from the first code file.
        source_code = source_bundle.code_files[0].content

        # Apply AST transformations to produce a "plagiarized" version.
        transformed_code = _transform_code(source_code, rng)

        # Compute similarity using all three methods.
        for method, compute_fn in (
            (SimilarityMethod.AST_BASED, _compute_ast_similarity),
            (SimilarityMethod.TOKEN_BASED, _compute_token_similarity),
            (SimilarityMethod.TEXT_BASED, _compute_text_similarity),
        ):
            sim_pct = compute_fn(source_code, transformed_code)
            all_scores.append(
                SimilarityScore(
                    sim_id=uuid.uuid4(),
                    submission_id=source_id,
                    compared_to=target_id,
                    method=method.value,
                    similarity_pct=round(sim_pct, 2),
                    flagged=sim_pct >= PLAGIARISM_THRESHOLD,
                )
            )

    # Step 5: Generate PLAGIARISM_SUSPECT tags.
    plag_tags = _generate_plagiarism_tags(plagiarism_sub_ids, rng)

    # Step 6: Generate background scores.
    bg_scores = _generate_background_scores(bundles, flagged_pair_set, rng)
    all_scores.extend(bg_scores)

    # Step 7: Select corrupted submissions and generate CORRUPTED tags.
    corrupted_ids = _select_corrupted_submissions(bundles, plagiarism_sub_ids, rng)
    corruption_tags = _generate_corruption_tags(corrupted_ids, rng)

    # Combine all tags.
    all_tags = plag_tags + corruption_tags

    return PlagiarismResult(
        similarity_scores=tuple(all_scores),
        tags=tuple(all_tags),
        corrupted_ids=tuple(corrupted_ids),
        plagiarism_pairs=tuple(plagiarism_pair_ids),
    )
