"""Canonical natural Object Counting Algebra, independent of record storage.

Indices order all natural multiplicity vectors by cardinality and then ascending
lexicographic order. Division returns complete fibers, including symbolic free
coordinates; an exhausted operational budget never claims a partial theorem.
"""

from collections.abc import Sequence as imp_3010_Sequence
from dataclasses import dataclass as imp_3011_dataclass
from hashlib import sha256 as imp_3012_sha256
from json import dumps as imp_3013_dumps
from math import comb as imp_3014_comb


@imp_3011_dataclass(frozen=True, init=False)
class type_3000_domain:
    """Immutable, explicitly ordered alphabet and composition-independent index."""

    attr_3006_alphabet: tuple[str, ...]
    attr_3001_namespace: str

    def __init__(arg_3015_self, arg_3016_alphabet: imp_3010_Sequence[str]):
        """Validate an ordered alphabet; its exact spelling determines the index."""
        if (not isinstance(arg_3016_alphabet, imp_3010_Sequence)
                or isinstance(arg_3016_alphabet, (str, bytes))
                or not arg_3016_alphabet
                or any(not isinstance(var_3017_symbol, str) or not var_3017_symbol
                       for var_3017_symbol in arg_3016_alphabet)
                or len(set(arg_3016_alphabet)) != len(arg_3016_alphabet)):
            raise ValueError("alphabet must be a nonempty ordered sequence of unique nonempty strings")
        var_3018_alphabet = tuple(arg_3016_alphabet)
        var_3019_profile = {
            "version": 1, "domain": "N0^d", "alphabet": var_3018_alphabet,
            "equality": "coordinatewise", "origin": 0,
            "order": "cardinality-then-ascending-lexicographic",
        }
        var_3020_namespace = "oca-" + imp_3012_sha256(
            imp_3013_dumps(var_3019_profile, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        object.__setattr__(arg_3015_self, "attr_3006_alphabet", var_3018_alphabet)
        object.__setattr__(arg_3015_self, "attr_3001_namespace", var_3020_namespace)


def fn_3021_natural(arg_3022_value: object, arg_3023_label: str) -> int:
    """Reject negative, boolean, and noninteger multiplicities or addresses."""
    if isinstance(arg_3022_value, bool) or not isinstance(arg_3022_value, int) or arg_3022_value < 0:
        raise ValueError(arg_3023_label + " must be a nonnegative integer")
    return arg_3022_value


def fn_3024_configuration(arg_3025_domain: type_3000_domain,
                          arg_3026_configuration: object) -> tuple[int, ...]:
    """Validate a vector against the complete natural domain."""
    if not isinstance(arg_3025_domain, type_3000_domain):
        raise ValueError("domain must be a type_3000_domain")
    if (not isinstance(arg_3026_configuration, imp_3010_Sequence)
            or isinstance(arg_3026_configuration, (str, bytes))
            or len(arg_3026_configuration) != len(arg_3025_domain.attr_3006_alphabet)):
        raise ValueError("configuration must have one coordinate per alphabet symbol")
    return tuple(fn_3021_natural(var_3027_coordinate, "coordinate")
                 for var_3027_coordinate in arg_3026_configuration)


def fn_3002_encode(arg_3025_domain: type_3000_domain,
                   arg_3026_configuration: imp_3010_Sequence[int]) -> int:
    """Rank a configuration using telescoping binomial block counts."""
    var_3028_vector = fn_3024_configuration(arg_3025_domain, arg_3026_configuration)
    var_3029_dimension = len(var_3028_vector)
    var_3032_remaining = sum(var_3028_vector)
    var_3033_rank = imp_3014_comb(var_3032_remaining + var_3029_dimension - 1, var_3029_dimension)
    for var_3034_index, var_3027_coordinate in enumerate(var_3028_vector[:-1]):
        var_3035_tail = var_3029_dimension - var_3034_index - 1
        var_3033_rank += (
            imp_3014_comb(var_3032_remaining + var_3035_tail, var_3035_tail)
            - imp_3014_comb(var_3032_remaining - var_3027_coordinate + var_3035_tail, var_3035_tail)
        )
        var_3032_remaining -= var_3027_coordinate
    return var_3033_rank


def fn_3003_decode(arg_3025_domain: type_3000_domain, arg_3036_id: int) -> tuple[int, ...]:
    """Unrank through logarithmic shell and coordinate searches."""
    if not isinstance(arg_3025_domain, type_3000_domain):
        raise ValueError("domain must be a type_3000_domain")
    fn_3021_natural(arg_3036_id, "configuration ID")
    var_3029_dimension = len(arg_3025_domain.attr_3006_alphabet)
    if var_3029_dimension == 1:
        return (arg_3036_id,)
    var_3037_low, var_3038_high = 0, 1
    while imp_3014_comb(var_3038_high + var_3029_dimension - 1, var_3029_dimension) <= arg_3036_id:
        var_3038_high *= 2
    while var_3038_high - var_3037_low > 1:
        var_3039_middle = (var_3037_low + var_3038_high) // 2
        if imp_3014_comb(var_3039_middle + var_3029_dimension - 1, var_3029_dimension) <= arg_3036_id:
            var_3037_low = var_3039_middle
        else:
            var_3038_high = var_3039_middle
    var_3032_remaining = var_3037_low
    var_3040_offset = arg_3036_id - imp_3014_comb(var_3032_remaining + var_3029_dimension - 1, var_3029_dimension)
    var_3041_coordinates = []
    for var_3034_index in range(var_3029_dimension - 1):
        var_3035_tail = var_3029_dimension - var_3034_index - 1
        var_3042_block = imp_3014_comb(var_3032_remaining + var_3035_tail, var_3035_tail)
        var_3037_low, var_3038_high = 0, var_3032_remaining + 1
        while var_3038_high - var_3037_low > 1:
            var_3039_middle = (var_3037_low + var_3038_high) // 2
            var_3043_skipped = var_3042_block - imp_3014_comb(
                var_3032_remaining - var_3039_middle + var_3035_tail, var_3035_tail)
            if var_3043_skipped <= var_3040_offset:
                var_3037_low = var_3039_middle
            else:
                var_3038_high = var_3039_middle
        var_3040_offset -= var_3042_block - imp_3014_comb(
            var_3032_remaining - var_3037_low + var_3035_tail, var_3035_tail)
        var_3041_coordinates.append(var_3037_low)
        var_3032_remaining -= var_3037_low
    var_3041_coordinates.append(var_3032_remaining)
    return tuple(var_3041_coordinates)


class type_3031_limit(RuntimeError):
    """Internal control flow for exhausted computation budgets."""


class type_3030_budget:
    """Shared operation counter, including nested property checks."""

    def __init__(arg_3015_self, arg_3044_max_steps: int):
        arg_3015_self.attr_3045_remaining = fn_3021_natural(arg_3044_max_steps, "max_steps")

    def fn_3046_tick(arg_3015_self):
        """Consume one finite search/check step or stop without a conclusion."""
        if arg_3015_self.attr_3045_remaining == 0:
            raise type_3031_limit()
        arg_3015_self.attr_3045_remaining -= 1


def fn_3047_tensor(arg_3025_domain: type_3000_domain,
                   arg_3048_composition: object) -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Require every primitive pair's full nonnegative output vector."""
    if not isinstance(arg_3025_domain, type_3000_domain):
        raise ValueError("domain must be a type_3000_domain")
    var_3029_dimension = len(arg_3025_domain.attr_3006_alphabet)
    if (not isinstance(arg_3048_composition, imp_3010_Sequence)
            or isinstance(arg_3048_composition, (str, bytes))
            or len(arg_3048_composition) != var_3029_dimension):
        raise ValueError("composition must be a complete dimension-cubed tensor")
    var_3049_tensor = []
    for var_3050_row in arg_3048_composition:
        if (not isinstance(var_3050_row, imp_3010_Sequence)
                or isinstance(var_3050_row, (str, bytes))
                or len(var_3050_row) != var_3029_dimension):
            raise ValueError("composition must be a complete dimension-cubed tensor")
        var_3049_tensor.append(tuple(fn_3024_configuration(arg_3025_domain, var_3051_output)
                                     for var_3051_output in var_3050_row))
    return tuple(var_3049_tensor)


def fn_3052_operand(arg_3025_domain: type_3000_domain, arg_3022_value: object) -> tuple[int, ...]:
    """Decode an ID or validate an explicitly supplied multiplicity vector."""
    if isinstance(arg_3022_value, int):
        return fn_3003_decode(arg_3025_domain, arg_3022_value)
    return fn_3024_configuration(arg_3025_domain, arg_3022_value)


def fn_3053_value(arg_3025_domain: type_3000_domain, arg_3026_configuration: imp_3010_Sequence[int]) -> dict:
    """Create the disjoint, successful single-configuration result."""
    return {"status": "ok", "outcome": {"kind": "value",
            "id": fn_3002_encode(arg_3025_domain, arg_3026_configuration),
            "configuration": list(arg_3026_configuration)}}


def fn_3054_fiber(arg_3055_matrix: list[list[int]], arg_3056_target: tuple[int, ...],
                  arg_3057_budget: type_3030_budget, arg_3058_max_solutions: int) -> tuple[list[tuple[int, ...]], list[int]]:
    """Exactly solve a rectangular nonnegative system, separating zero columns.

    DFS is iterative. A row with a single remaining nonzero coefficient fixes a
    coordinate directly, which makes scalar and diagonal huge-integer systems
    practical. Every searched candidate consumes a step. Bases set all free
    coordinates to zero and are complete only if this routine returns normally.
    """
    var_3029_dimension = len(arg_3055_matrix[0])
    var_3059_columns = [tuple(var_3050_row[var_3034_index] for var_3050_row in arg_3055_matrix)
                        for var_3034_index in range(var_3029_dimension)]
    var_3060_free = [var_3034_index for var_3034_index, var_3061_column in enumerate(var_3059_columns)
                     if not any(var_3061_column)]
    var_3062_bounded = tuple(var_3034_index for var_3034_index in range(var_3029_dimension)
                            if var_3034_index not in var_3060_free)
    var_3063_solutions = []
    # Stack frames hold (remaining columns, residual, assigned vector, candidate iterator).
    var_3064_stack = [(var_3062_bounded, arg_3056_target, (0,) * var_3029_dimension, None)]
    while var_3064_stack:
        var_3065_active, var_3066_residual, var_3067_assigned, var_3068_iterator = var_3064_stack.pop()
        arg_3057_budget.fn_3046_tick()
        if not var_3065_active:
            if not any(var_3066_residual):
                if len(var_3063_solutions) >= arg_3058_max_solutions:
                    raise type_3031_limit()
                var_3063_solutions.append(var_3067_assigned)
            continue
        if var_3068_iterator is None:
            var_3069_forced = {}
            var_3070_impossible = False
            for var_3071_row_index, var_3072_amount in enumerate(var_3066_residual):
                var_3073_nonzero = [var_3034_index for var_3034_index in var_3065_active
                                    if var_3059_columns[var_3034_index][var_3071_row_index]]
                if not var_3073_nonzero:
                    if var_3072_amount:
                        var_3070_impossible = True
                        break
                elif len(var_3073_nonzero) == 1:
                    var_3074_coordinate = var_3073_nonzero[0]
                    var_3075_quotient, var_3076_remainder = divmod(
                        var_3072_amount, var_3059_columns[var_3074_coordinate][var_3071_row_index])
                    if var_3076_remainder or (var_3074_coordinate in var_3069_forced
                            and var_3069_forced[var_3074_coordinate] != var_3075_quotient):
                        var_3070_impossible = True
                        break
                    var_3069_forced[var_3074_coordinate] = var_3075_quotient
            if var_3070_impossible:
                continue
            var_3074_coordinate = next(iter(var_3069_forced), var_3065_active[0])
            var_3065_active = (var_3074_coordinate,) + tuple(
                var_3034_index for var_3034_index in var_3065_active if var_3034_index != var_3074_coordinate)
            var_3077_bound = min(
                var_3072_amount // var_3078_coefficient
                for var_3072_amount, var_3078_coefficient in zip(var_3066_residual, var_3059_columns[var_3074_coordinate])
                if var_3078_coefficient)
            if var_3069_forced:
                var_3075_quotient = var_3069_forced[var_3074_coordinate]
                if var_3075_quotient > var_3077_bound:
                    continue
                var_3068_iterator = iter((var_3075_quotient,))
            else:
                var_3068_iterator = iter(range(var_3077_bound + 1))
        var_3074_coordinate = var_3065_active[0]
        try:
            var_3075_quotient = next(var_3068_iterator)
        except StopIteration:
            continue
        var_3064_stack.append((var_3065_active, var_3066_residual, var_3067_assigned, var_3068_iterator))
        var_3079_next_vector = list(var_3067_assigned)
        var_3079_next_vector[var_3074_coordinate] = var_3075_quotient
        var_3080_next_residual = tuple(
            var_3072_amount - var_3075_quotient * var_3078_coefficient
            for var_3072_amount, var_3078_coefficient in zip(var_3066_residual, var_3059_columns[var_3074_coordinate]))
        var_3064_stack.append((var_3065_active[1:], var_3080_next_residual, tuple(var_3079_next_vector), None))
    return var_3063_solutions, var_3060_free


def fn_3004_evaluate(arg_3025_domain: type_3000_domain, arg_3081_operation: str,
                     arg_3082_left: object, arg_3083_right: object,
                     arg_3048_composition: object = None, arg_3044_max_steps: int = 500000,
                     arg_3058_max_solutions: int = 10000) -> dict:
    """Transport configuration operations through canonical IDs.

    divide_right(x,y) solves q*y=x; divide_left(x,y) solves y*q=x.
    Inputs may be IDs or coordinate sequences. Only multiplication and division
    require a complete explicit composition tensor; no default is inferred.
    """
    var_3084_left = fn_3052_operand(arg_3025_domain, arg_3082_left)
    var_3085_right = fn_3052_operand(arg_3025_domain, arg_3083_right)
    var_3086_budget = type_3030_budget(arg_3044_max_steps)
    fn_3021_natural(arg_3058_max_solutions, "max_solutions")
    if arg_3081_operation not in ("add", "subtract", "multiply", "divide_right", "divide_left"):
        raise ValueError("unknown algebra operation")
    var_3049_tensor = (fn_3047_tensor(arg_3025_domain, arg_3048_composition)
                       if arg_3081_operation in ("multiply", "divide_right", "divide_left") else None)
    var_3029_dimension = len(var_3084_left)
    try:
        var_3086_budget.fn_3046_tick()
        if arg_3081_operation == "add":
            return fn_3053_value(arg_3025_domain, tuple(
                var_3087_a + var_3088_b for var_3087_a, var_3088_b in zip(var_3084_left, var_3085_right)))
        if arg_3081_operation == "subtract":
            var_3089_deficits = [max(0, var_3088_b - var_3087_a)
                                 for var_3087_a, var_3088_b in zip(var_3084_left, var_3085_right)]
            if any(var_3089_deficits):
                return {"status": "ok", "outcome": {"kind": "undefined", "deficits": var_3089_deficits}}
            return fn_3053_value(arg_3025_domain, tuple(
                var_3087_a - var_3088_b for var_3087_a, var_3088_b in zip(var_3084_left, var_3085_right)))
        if arg_3081_operation == "multiply":
            var_3090_product = [0] * var_3029_dimension
            for var_3091_i in range(var_3029_dimension):
                for var_3092_j in range(var_3029_dimension):
                    for var_3093_k in range(var_3029_dimension):
                        var_3086_budget.fn_3046_tick()
                        var_3090_product[var_3093_k] += (var_3084_left[var_3091_i] * var_3085_right[var_3092_j]
                            * var_3049_tensor[var_3091_i][var_3092_j][var_3093_k])
            return fn_3053_value(arg_3025_domain, var_3090_product)
        var_3094_matrix = [[0] * var_3029_dimension for var_3093_k in range(var_3029_dimension)]
        for var_3093_k in range(var_3029_dimension):
            for var_3091_i in range(var_3029_dimension):
                for var_3092_j in range(var_3029_dimension):
                    var_3086_budget.fn_3046_tick()
                    var_3094_matrix[var_3093_k][var_3091_i] += var_3085_right[var_3092_j] * (
                        var_3049_tensor[var_3091_i][var_3092_j][var_3093_k] if arg_3081_operation == "divide_right"
                        else var_3049_tensor[var_3092_j][var_3091_i][var_3093_k])
        var_3063_solutions, var_3060_free = fn_3054_fiber(
            var_3094_matrix, var_3084_left, var_3086_budget, arg_3058_max_solutions)
        var_3063_solutions.sort(key=lambda arg_3095_vector: fn_3002_encode(arg_3025_domain, arg_3095_vector))
        if var_3060_free and var_3063_solutions:
            return {"status": "ok", "outcome": {"kind": "solutions", "finite": False,
                "bases": [list(var_3028_vector) for var_3028_vector in var_3063_solutions],
                "base_ids": [fn_3002_encode(arg_3025_domain, var_3028_vector) for var_3028_vector in var_3063_solutions],
                "free_coordinates": var_3060_free,
                "parameterization": "q = base + sum(t_i * e_i for i in free_coordinates), t_i in N0; id = encode(q)",
                "namespace": arg_3025_domain.attr_3001_namespace}}
        return {"status": "ok", "outcome": {"kind": "solutions", "finite": True,
            "ids": [fn_3002_encode(arg_3025_domain, var_3028_vector) for var_3028_vector in var_3063_solutions],
            "configurations": [list(var_3028_vector) for var_3028_vector in var_3063_solutions]}}
    except type_3031_limit:
        return {"status": "resource_limit", "outcome": None}


def fn_3005_laws(arg_3025_domain: type_3000_domain, arg_3048_composition: object,
                 arg_3044_max_steps: int = 500000) -> dict:
    """Certify tensor laws on primitive bases and recover a natural identity.

    The two-sided identity system searches all natural configurations, including
    composite identities. No partial classification survives budget exhaustion.
    """
    var_3049_tensor = fn_3047_tensor(arg_3025_domain, arg_3048_composition)
    var_3029_dimension = len(arg_3025_domain.attr_3006_alphabet)
    var_3086_budget = type_3030_budget(arg_3044_max_steps)
    var_3096_commutative, var_3097_associative = True, True
    try:
        for var_3091_i in range(var_3029_dimension):
            for var_3092_j in range(var_3029_dimension):
                var_3086_budget.fn_3046_tick()
                if var_3049_tensor[var_3091_i][var_3092_j] != var_3049_tensor[var_3092_j][var_3091_i]:
                    var_3096_commutative = False
                for var_3093_k in range(var_3029_dimension):
                    for var_3098_output in range(var_3029_dimension):
                        var_3099_first, var_3100_second = 0, 0
                        for var_3101_middle in range(var_3029_dimension):
                            var_3086_budget.fn_3046_tick()
                            var_3099_first += (var_3049_tensor[var_3091_i][var_3092_j][var_3101_middle]
                                * var_3049_tensor[var_3101_middle][var_3093_k][var_3098_output])
                            var_3100_second += (var_3049_tensor[var_3092_j][var_3093_k][var_3101_middle]
                                * var_3049_tensor[var_3091_i][var_3101_middle][var_3098_output])
                        if var_3099_first != var_3100_second:
                            var_3097_associative = False
        var_3094_matrix, var_3102_target = [], []
        for var_3092_j in range(var_3029_dimension):
            for var_3093_k in range(var_3029_dimension):
                var_3086_budget.fn_3046_tick()
                var_3094_matrix.append([var_3049_tensor[var_3091_i][var_3092_j][var_3093_k]
                                        for var_3091_i in range(var_3029_dimension)])
                var_3102_target.append(int(var_3092_j == var_3093_k))
                var_3094_matrix.append([var_3049_tensor[var_3092_j][var_3091_i][var_3093_k]
                                        for var_3091_i in range(var_3029_dimension)])
                var_3102_target.append(int(var_3092_j == var_3093_k))
        var_3063_solutions, var_3060_free = fn_3054_fiber(
            var_3094_matrix, tuple(var_3102_target), var_3086_budget, 2)
        var_3103_identity = ({"id": fn_3002_encode(arg_3025_domain, var_3063_solutions[0]),
                              "configuration": list(var_3063_solutions[0])} if var_3063_solutions else None)
        var_3104_primitive_identity = bool(var_3063_solutions and sum(var_3063_solutions[0]) == 1)
        var_3105_singleton_products = all(sum(var_3051_output) == 1
                                         for var_3050_row in var_3049_tensor for var_3051_output in var_3050_row)
        var_3106_classification = ("commutative_unital_semiring" if var_3096_commutative else "unital_semiring") if (
            var_3097_associative and var_3103_identity is not None) else (
            "associative_bilinear_algebra" if var_3097_associative else "nonassociative_bilinear_algebra")
        return {"status": "ok", "laws": {
            "commutative": var_3096_commutative, "associative": var_3097_associative,
            "identity": var_3103_identity, "primitive_identity": var_3104_primitive_identity,
            "finite_monoid": var_3097_associative and var_3104_primitive_identity and var_3105_singleton_products,
            "cardinality_multiplicative": var_3105_singleton_products,
            "classification": var_3106_classification,
            "additive_structure": "free_commutative_monoid", "zero_absorbing": True,
            "distributive": True}}
    except type_3031_limit:
        return {"status": "resource_limit", "laws": None}
