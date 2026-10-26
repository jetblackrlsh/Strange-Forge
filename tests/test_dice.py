import unittest

from strange_forge.dice import assess_check, roll


class DiceTests(unittest.TestCase):
    def test_receipt(self):
        values = iter([0, 3, 5])
        receipt = roll(' 3d6 + 2 ', randbelow=lambda n: next(values))
        self.assertEqual(receipt['dice'], [1, 4, 6])
        self.assertEqual(receipt['total'], 13)
        self.assertEqual(receipt['expression'], '3d6+2')
        self.assertEqual(receipt['randomness'], 'injected')

    def test_negative(self):
        self.assertEqual(roll('1D20-3', randbelow=lambda n: 0)['total'], -2)

    def test_secure_default_receipt(self):
        result = roll('3d6')
        self.assertEqual(result['randomness'], 'secrets.randbelow')
        self.assertTrue(all(1 <= d <= 6 for d in result['dice']))
        self.assertEqual(sum(result['dice']), result['total'])

    def test_reject_invalid_or_unbounded(self):
        for expression in ['', '0d6', '101d6', '1d1', '1d1000001', '2d6+1000001',
                           '2d6+1d6', '__import__("os")', '1d6*10', '1d6' + ' ' * 81, None]:
            with self.subTest(expression=expression), self.assertRaises(ValueError):
                roll(expression)

    def test_reject_bad_rng(self):
        for value in [-1, 6, True, 1.2]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                roll('1d6', randbelow=lambda n: value)

    def test_degrees(self):
        cases = [([1, 1, 1], 0, 10, 'perfect_failure', 1, 0),
                 ([1, 2, 3], 0, 12, 'spectacular_failure', 1, 0),
                 ([2, 3, 4], 0, 10, 'failure', 1, 0),
                 ([3, 4, 5], 0, 10, 'success', 0, 0),
                 ([4, 5, 6], 1, 10, 'spectacular_success', 0, 1),
                 ([6, 6, 6], 0, 17, 'perfect_success', 0, 1),
                 ([1, 1, 1], 10, 12, 'perfect_success', 0, 1),
                 ([6, 6, 6], 0, 30, 'spectacular_failure', 1, 0)]
        for dice, mod, tc, degree, frustration, ego in cases:
            with self.subTest(degree=degree, dice=dice):
                result = assess_check(dice, mod, tc, tie_policy='failure')
                self.assertEqual(result['degree'], degree)
                self.assertEqual(result['proposed_frustration'], frustration)
                self.assertEqual(result['proposed_gm_ego'], ego)

    def test_tie_is_explicit_local_ruling(self):
        self.assertFalse(assess_check([2, 3, 4], 1, 10, tie_policy='failure')['success'])
        self.assertTrue(assess_check([2, 3, 4], 1, 10, tie_policy='success')['success'])
        with self.assertRaises(TypeError):
            assess_check([2, 3, 4], 1, 10)
        with self.assertRaises(ValueError):
            assess_check([2, 3, 4], 1, 10, tie_policy='canon')

    def test_bad_check_input(self):
        for dice in [[1, 2], [0, 1, 2], [1, True, 3], [1, 2, 7], '123']:
            with self.subTest(dice=dice), self.assertRaises(ValueError):
                assess_check(dice, 0, 10, tie_policy='failure')
        with self.assertRaises(ValueError):
            assess_check([1, 2, 3], True, 10, tie_policy='failure')

    def test_npc_awards_suppressed(self):
        for dice, tc in [([1, 1, 1], 10), ([6, 6, 6], 10)]:
            with self.subTest(dice=dice):
                result = assess_check(dice, 0, tc, tie_policy='failure', actor='npc')
                self.assertEqual(result['actor'], 'npc')
                self.assertEqual(result['proposed_frustration'], 0)
                self.assertEqual(result['proposed_gm_ego'], 0)
        self.assertEqual(assess_check([6, 6, 6], 0, 10, tie_policy='success')['actor'], 'pc')
        with self.assertRaises(ValueError):
            assess_check([1, 2, 3], 0, 10, tie_policy='failure', actor='villain')

    def test_no_mutation(self):
        dice = [2, 3, 4]
        result = assess_check(dice, 0, 10, tie_policy='failure')
        result['dice'][0] = 6
        self.assertEqual(dice, [2, 3, 4])


if __name__ == '__main__':
    unittest.main()
