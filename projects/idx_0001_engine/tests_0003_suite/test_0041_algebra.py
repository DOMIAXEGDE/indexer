"""Independent finite checks and source examples for the natural algebra."""

import itertools as imp_4001_itertools
import random as imp_4002_random
import unittest as imp_4003_unittest
from dataclasses import FrozenInstanceError as imp_4004_FrozenInstanceError

from pkg_0002_engine.mod_0011_algebra import (
    type_3000_domain, fn_3002_encode, fn_3003_decode, fn_3004_evaluate, fn_3005_laws,
)


class type_4000_algebra_tests(imp_4003_unittest.TestCase):
    """Check rank, exact fibers, typed outcomes, and certified composition laws."""

    def setUp(arg_4005_self):
        arg_4005_self.attr_4006_domain = type_3000_domain(("neutral", "toggle"))
        arg_4005_self.attr_4007_tensor = (((1, 0), (0, 1)), ((0, 1), (1, 0)))

    def test_4008_source_examples(arg_4005_self):
        var_4009_vectors = [(0, 0), (0, 1), (1, 0), (0, 2), (1, 1), (2, 0)]
        for var_4010_index, var_4011_vector in enumerate(var_4009_vectors):
            arg_4005_self.assertEqual(fn_3003_decode(arg_4005_self.attr_4006_domain, var_4010_index), var_4011_vector)
            arg_4005_self.assertEqual(fn_3002_encode(arg_4005_self.attr_4006_domain, var_4011_vector), var_4010_index)
        for var_4012_operation, var_4013_left, var_4014_right, var_4015_expected in (
                ("add", 1, 2, 4), ("subtract", 4, 1, 2), ("multiply", 1, 1, 2)):
            var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, var_4012_operation,
                var_4013_left, var_4014_right, arg_4005_self.attr_4007_tensor)
            arg_4005_self.assertEqual(var_4016_result["status"], "ok")
            arg_4005_self.assertEqual(var_4016_result["outcome"]["id"], var_4015_expected)
        for var_4012_operation in ("divide_right", "divide_left"):
            var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, var_4012_operation, 4, 4,
                                              arg_4005_self.attr_4007_tensor)
            arg_4005_self.assertEqual(var_4016_result["outcome"]["ids"], [1, 2])

    def test_4017_independent_small_enumeration(arg_4005_self):
        for var_4018_dimension in range(1, 6):
            var_4019_domain = type_3000_domain(tuple(str(var_4010_index) for var_4010_index in range(var_4018_dimension)))
            var_4009_vectors = sorted((var_4011_vector for var_4011_vector in imp_4001_itertools.product(
                range(6), repeat=var_4018_dimension) if sum(var_4011_vector) <= 5),
                key=lambda arg_4020_vector: (sum(arg_4020_vector), arg_4020_vector))
            for var_4010_index, var_4011_vector in enumerate(var_4009_vectors):
                arg_4005_self.assertEqual(fn_3002_encode(var_4019_domain, var_4011_vector), var_4010_index)
                arg_4005_self.assertEqual(fn_3003_decode(var_4019_domain, var_4010_index), var_4011_vector)

    def test_4021_large_integer_roundtrips(arg_4005_self):
        for var_4018_dimension in (1, 2, 5, 12):
            var_4019_domain = type_3000_domain(tuple(str(var_4010_index) for var_4010_index in range(var_4018_dimension)))
            for var_4022_id in (10**100, 2**1024 + 17):
                var_4011_vector = fn_3003_decode(var_4019_domain, var_4022_id)
                arg_4005_self.assertEqual(fn_3002_encode(var_4019_domain, var_4011_vector), var_4022_id)
            var_4011_vector = tuple(10**100 + var_4010_index for var_4010_index in range(var_4018_dimension))
            arg_4005_self.assertEqual(fn_3003_decode(var_4019_domain, fn_3002_encode(var_4019_domain, var_4011_vector)), var_4011_vector)

    def test_4023_namespace_and_immutability(arg_4005_self):
        var_4019_domain = type_3000_domain(["neutral", "toggle"])
        arg_4005_self.assertEqual(var_4019_domain.attr_3001_namespace, arg_4005_self.attr_4006_domain.attr_3001_namespace)
        arg_4005_self.assertNotEqual(var_4019_domain.attr_3001_namespace,
                                     type_3000_domain(["toggle", "neutral"]).attr_3001_namespace)
        arg_4005_self.assertNotEqual(var_4019_domain.attr_3001_namespace,
                                     type_3000_domain(["neutral", "toggle", "extra"]).attr_3001_namespace)
        var_4024_before = var_4019_domain.attr_3001_namespace
        fn_3005_laws(var_4019_domain, arg_4005_self.attr_4007_tensor)
        arg_4005_self.assertEqual(var_4019_domain.attr_3001_namespace, var_4024_before)
        with arg_4005_self.assertRaises(imp_4004_FrozenInstanceError):
            var_4019_domain.attr_3006_alphabet = ("changed",)

    def test_4025_invalid_inputs(arg_4005_self):
        for var_4026_invalid in ([], "word", ["a", "a"], [""], [1]):
            with arg_4005_self.assertRaises(ValueError):
                type_3000_domain(var_4026_invalid)
        for var_4026_invalid in (True, -1, 1.5, "3", None):
            with arg_4005_self.assertRaises(ValueError):
                fn_3003_decode(arg_4005_self.attr_4006_domain, var_4026_invalid)
        for var_4026_invalid in ((0,), (0, 0, 0), (True, 0), (-1, 0), (0.0, 0), "00"):
            with arg_4005_self.assertRaises(ValueError):
                fn_3002_encode(arg_4005_self.attr_4006_domain, var_4026_invalid)
        for var_4026_invalid in (None, [], [[0, 1], [0, 1]], [[[True, 0], [0, 1]], [[0, 1], [1, 0]]]):
            with arg_4005_self.assertRaises(ValueError):
                fn_3004_evaluate(arg_4005_self.attr_4006_domain, "multiply", 1, 2, var_4026_invalid)
        with arg_4005_self.assertRaises(ValueError):
            fn_3004_evaluate(arg_4005_self.attr_4006_domain, "unknown", 1, 2)
        with arg_4005_self.assertRaises(ValueError):
            fn_3004_evaluate(arg_4005_self.attr_4006_domain, "add", True, 2)
        with arg_4005_self.assertRaises(ValueError):
            fn_3004_evaluate(arg_4005_self.attr_4006_domain, "add", 1, 2, None, -1)
        with arg_4005_self.assertRaises(ValueError):
            fn_3004_evaluate(arg_4005_self.attr_4006_domain, "add", 1, 2, None, 100, True)

    def test_4027_disjoint_zero_outcomes(arg_4005_self):
        var_4028_zero = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "subtract", 4, 4)["outcome"]
        var_4029_empty = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", 1, 0,
                                         arg_4005_self.attr_4007_tensor)["outcome"]
        var_4030_singleton = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", 0, 1,
                                             arg_4005_self.attr_4007_tensor)["outcome"]
        var_4031_undefined = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "subtract", 1, 2)["outcome"]
        arg_4005_self.assertEqual(var_4028_zero, {"kind": "value", "id": 0, "configuration": [0, 0]})
        arg_4005_self.assertEqual(var_4029_empty, {"kind": "solutions", "finite": True, "ids": [], "configurations": []})
        arg_4005_self.assertEqual(var_4030_singleton, {"kind": "solutions", "finite": True, "ids": [0], "configurations": [[0, 0]]})
        arg_4005_self.assertEqual(var_4031_undefined, {"kind": "undefined", "deficits": [1, 0]})

    def test_4032_noncommuting_orientations(arg_4005_self):
        var_4033_tensor = (((1, 0), (1, 0)), ((0, 1), (0, 1)))
        var_4034_right = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", (0, 1), (1, 0), var_4033_tensor)
        var_4035_left = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_left", (0, 1), (1, 0), var_4033_tensor)
        arg_4005_self.assertEqual(var_4034_right["outcome"]["configurations"], [[0, 1]])
        arg_4005_self.assertEqual(var_4035_left["outcome"]["configurations"], [])
        var_4036_laws = fn_3005_laws(arg_4005_self.attr_4006_domain, var_4033_tensor)["laws"]
        arg_4005_self.assertFalse(var_4036_laws["commutative"])
        arg_4005_self.assertTrue(var_4036_laws["associative"])
        arg_4005_self.assertIsNone(var_4036_laws["identity"])

    def test_4037_annihilators_and_infinite_fibers(arg_4005_self):
        var_4033_tensor = (((1, 0), (0, 0)), ((0, 0), (0, 1)))
        var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", (2, 0), (1, 0), var_4033_tensor)
        arg_4005_self.assertFalse(var_4016_result["outcome"]["finite"])
        arg_4005_self.assertEqual(var_4016_result["outcome"]["bases"], [[2, 0]])
        arg_4005_self.assertEqual(var_4016_result["outcome"]["free_coordinates"], [1])
        for var_4038_parameter in (0, 1, 100000):
            arg_4005_self.assertEqual(fn_3004_evaluate(arg_4005_self.attr_4006_domain, "multiply",
                (2, var_4038_parameter), (1, 0), var_4033_tensor)["outcome"]["configuration"], [2, 0])
        var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", (0, 1), (1, 0), var_4033_tensor)
        arg_4005_self.assertEqual(var_4016_result["outcome"]["ids"], [])
        var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", 0, 0, var_4033_tensor)
        arg_4005_self.assertEqual(var_4016_result["outcome"]["bases"], [[0, 0]])
        arg_4005_self.assertEqual(var_4016_result["outcome"]["free_coordinates"], [0, 1])

    def test_4039_laws_composite_identity(arg_4005_self):
        var_4036_laws = fn_3005_laws(arg_4005_self.attr_4006_domain, arg_4005_self.attr_4007_tensor)["laws"]
        arg_4005_self.assertTrue(var_4036_laws["finite_monoid"])
        arg_4005_self.assertEqual(var_4036_laws["identity"], {"id": 2, "configuration": [1, 0]})
        arg_4005_self.assertEqual(var_4036_laws["classification"], "commutative_unital_semiring")
        var_4033_tensor = (((1, 0), (0, 0)), ((0, 0), (0, 1)))
        var_4036_laws = fn_3005_laws(arg_4005_self.attr_4006_domain, var_4033_tensor)["laws"]
        arg_4005_self.assertEqual(var_4036_laws["identity"], {"id": 4, "configuration": [1, 1]})
        arg_4005_self.assertFalse(var_4036_laws["primitive_identity"])
        arg_4005_self.assertFalse(var_4036_laws["finite_monoid"])
        var_4033_tensor = (((0, 1), (1, 0)), ((1, 0), (0, 0)))
        arg_4005_self.assertFalse(fn_3005_laws(arg_4005_self.attr_4006_domain, var_4033_tensor)["laws"]["associative"])
        arg_4005_self.assertIsNone(fn_3005_laws(type_3000_domain(["a"]), (((2,),),))["laws"]["identity"])

    def test_4040_resource_limits_never_partial(arg_4005_self):
        var_4041_expected = {"status": "resource_limit", "outcome": None}
        arg_4005_self.assertEqual(fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", 4, 4,
                                  arg_4005_self.attr_4007_tensor, 1), var_4041_expected)
        arg_4005_self.assertEqual(fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", 4, 4,
                                  arg_4005_self.attr_4007_tensor, 500000, 1), var_4041_expected)
        arg_4005_self.assertEqual(fn_3004_evaluate(arg_4005_self.attr_4006_domain, "add", 0, 0, None, 0), var_4041_expected)
        arg_4005_self.assertEqual(fn_3005_laws(arg_4005_self.attr_4006_domain, arg_4005_self.attr_4007_tensor, 1),
                                  {"status": "resource_limit", "laws": None})

    def test_4042_huge_scalar_and_diagonal_fibers(arg_4005_self):
        var_4019_domain = type_3000_domain(["a"])
        var_4016_result = fn_3004_evaluate(var_4019_domain, "divide_right", (10**200,), (2,), (((1,),),), 100)
        arg_4005_self.assertEqual(var_4016_result["outcome"]["configurations"], [[5 * 10**199]])
        var_4033_tensor = (((1, 0), (0, 0)), ((0, 0), (0, 1)))
        var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, "divide_right", (10**100, 10**100),
                                          (2, 4), var_4033_tensor, 100)
        arg_4005_self.assertEqual(var_4016_result["outcome"]["configurations"], [[5 * 10**99, 25 * 10**98]])

    def test_4043_random_fibers_against_brute_force(arg_4005_self):
        var_4044_random = imp_4002_random.Random(44)
        for var_4045_trial in range(100):
            var_4033_tensor = tuple(tuple(tuple(var_4044_random.randrange(3) for var_4046_k in range(2))
                for var_4047_j in range(2)) for var_4048_i in range(2))
            var_4049_target = tuple(var_4044_random.randrange(4) for var_4046_k in range(2))
            var_4050_divisor = tuple(var_4044_random.randrange(3) for var_4046_k in range(2))
            for var_4012_operation in ("divide_right", "divide_left"):
                var_4051_columns = [tuple(sum(var_4050_divisor[var_4047_j] * (
                    var_4033_tensor[var_4048_i][var_4047_j][var_4046_k] if var_4012_operation == "divide_right"
                    else var_4033_tensor[var_4047_j][var_4048_i][var_4046_k]) for var_4047_j in range(2))
                    for var_4046_k in range(2)) for var_4048_i in range(2)]
                var_4052_free = [var_4048_i for var_4048_i in range(2) if not any(var_4051_columns[var_4048_i])]
                var_4053_expected = set()
                for var_4054_candidate in imp_4001_itertools.product(range(4), repeat=2):
                    if any(var_4054_candidate[var_4048_i] for var_4048_i in var_4052_free):
                        continue
                    var_4055_actual = tuple(sum(var_4054_candidate[var_4048_i] * var_4051_columns[var_4048_i][var_4046_k]
                        for var_4048_i in range(2)) for var_4046_k in range(2))
                    if var_4055_actual == var_4049_target:
                        var_4053_expected.add(var_4054_candidate)
                var_4016_result = fn_3004_evaluate(arg_4005_self.attr_4006_domain, var_4012_operation,
                    var_4049_target, var_4050_divisor, var_4033_tensor)
                arg_4005_self.assertEqual(var_4016_result["status"], "ok")
                var_4056_outcome = var_4016_result["outcome"]
                var_4057_key = "bases" if not var_4056_outcome["finite"] else "configurations"
                arg_4005_self.assertEqual({tuple(var_4011_vector) for var_4011_vector in var_4056_outcome[var_4057_key]}, var_4053_expected)
                arg_4005_self.assertEqual(var_4056_outcome["finite"], not (var_4052_free and var_4053_expected))


if __name__ == "__main__":
    imp_4003_unittest.main()
