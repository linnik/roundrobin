import unittest

import roundrobin


class WeightCase(unittest.TestCase):

    def test_empty_dataset(self):
        with self.assertRaises(ValueError):
            roundrobin.basic([])
        with self.assertRaises(ValueError):
            roundrobin.smooth([])
        with self.assertRaises(ValueError):
            roundrobin.smooth_stateful([])
        with self.assertRaises(ValueError):
            roundrobin.weighted([])

    def test_negative_weights_raise(self):
        with self.assertRaises(ValueError):
            roundrobin.smooth([("A", -1)])
        with self.assertRaises(ValueError):
            roundrobin.smooth_stateful([("A", -1)])

    def test_basic(self):
        data = ["A", "B", "C"]
        get_next = roundrobin.basic(data)
        result = ''.join([get_next() for _ in range(7)])
        self.assertEqual(result, 'ABCABCA')

    def test_smooth(self):
        data = [("A", 5), ("B", 1), ("C", 1)]
        get_next = roundrobin.smooth(data)
        result = ''.join([get_next() for _ in range(7)])
        self.assertEqual(result, 'AABACAA')

    def test_smooth_single_item(self):
        get_next = roundrobin.smooth([("A", 5)])
        result = ''.join([get_next() for _ in range(7)])
        self.assertEqual(result, 'AAAAAAA')

    def test_smooth_allows_unhashable_keys(self):
        a = [1]
        b = [2]
        get_next = roundrobin.smooth([(a, 1), (b, 1)])
        self.assertTrue(get_next() is a)
        self.assertTrue(get_next() is b)

    def test_smooth_repeats_on_total_weight(self):
        data = [("A", 5), ("B", 1), ("C", 1)]
        get_next = roundrobin.smooth(data)
        result = ''.join([get_next() for _ in range(14)])
        self.assertEqual(result, 'AABACAAAABACAA')

    def test_smooth_distribution(self):
        data = [("A", 5), ("B", 1), ("C", 1)]
        get_next = roundrobin.smooth(data)
        cnt = {}
        for _ in range(70):
            key = get_next()
            cnt[key] = cnt.get(key, 0) + 1
        self.assertTrue(cnt['A'] == 50)
        self.assertTrue(cnt['B'] == 10)
        self.assertTrue(cnt['C'] == 10)

    def test_itemweight_repr_includes_disabled(self):

        item = roundrobin.smooth_rr.ItemWeight("A", 1)
        self.assertIn("key='A'", repr(item))
        item.disabled = True
        self.assertIn("disabled=True", repr(item))

    def test_smooth_stateful_slow_start(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)], initial_effective={"A": 0})
        result = ''.join([rr() for _ in range(7)])
        self.assertEqual(result, 'BCAABAA')

    def test_smooth_stateful_single_item_ramps(self):
        rr = roundrobin.smooth_stateful([("A", 5)], initial_effective=0)
        item_a = [x for x in rr.items if x.key == "A"][0]
        self.assertEqual(item_a.effective_weight, 0)
        rr()
        rr()
        rr()
        self.assertEqual(item_a.effective_weight, 3)

    def test_smooth_stateful_allows_unhashable_keys(self):
        a = [1]
        b = [2]
        rr = roundrobin.smooth_stateful([(a, 1), (b, 1)])
        item_a = [x for x in rr.items if x.key is a][0]
        item_b = [x for x in rr.items if x.key is b][0]

        rr.disable(a)
        self.assertEqual(item_a.effective_weight, 0)
        self.assertEqual(item_b.effective_weight, 1)
        self.assertTrue(rr() is b)
        self.assertEqual(item_a.effective_weight, 0)

    def test_smooth_stateful_ramps_effective_weight(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)], initial_effective={"A": 0})
        item_a = [x for x in rr.items if x.key == "A"][0]
        self.assertEqual(item_a.effective_weight, 0)
        rr()
        rr()
        rr()
        self.assertEqual(item_a.effective_weight, 3)

    def test_smooth_stateful_set_effective_clamps(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        rr.set("A", effective=-10)
        self.assertEqual(item_a.effective_weight, 0)
        rr.set("A", effective=999)
        self.assertEqual(item_a.effective_weight, 5)

    def test_smooth_stateful_reset_defaults_to_weight(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        rr.set("A", effective=0)
        self.assertEqual(item_a.effective_weight, 0)
        rr.reset("A")
        self.assertEqual(item_a.effective_weight, 5)

    def test_smooth_stateful_set_effective_scales_current_weight_down(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]

        item_a.current_weight = 100
        rr.set("A", effective=1)
        self.assertEqual(item_a.effective_weight, 1)
        self.assertEqual(item_a.current_weight, 20)

        item_a.current_weight = 100
        rr.set("A", effective=0)
        self.assertEqual(item_a.effective_weight, 0)
        self.assertEqual(item_a.current_weight, 0)

    def test_smooth_stateful_set_weight_decrease_clamps_effective(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        item_a.current_weight = 100
        rr.set("A", weight=2)
        self.assertEqual(item_a.weight, 2)
        self.assertEqual(item_a.effective_weight, 2)
        self.assertEqual(item_a.current_weight, 40)

    def test_smooth_stateful_set_weight_decrease_scales_current_weight(self):
        rr = roundrobin.smooth_stateful([("A", 100), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        item_b = [x for x in rr.items if x.key == "B"][0]

        item_a.current_weight = 100
        item_b.current_weight = 0
        rr.set("A", weight=1)

        result = ''.join([rr() for _ in range(4)])
        self.assertEqual(result, 'ABAB')

    def test_smooth_stateful_set_weight_increase_allows_ramp(self):
        rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        rr.set("A", weight=3)
        self.assertEqual(item_a.weight, 3)
        self.assertEqual(item_a.effective_weight, 1)
        rr()
        rr()
        self.assertEqual(item_a.effective_weight, 3)

    def test_smooth_stateful_set_unknown_key(self):
        rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
        with self.assertRaises(KeyError):
            rr.set("missing", weight=1)
        with self.assertRaises(KeyError):
            rr.set("missing", effective=1)

    def test_smooth_stateful_set_weight_negative_raises(self):
        rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
        with self.assertRaises(ValueError):
            rr.set("A", weight=-1)

    def test_smooth_stateful_initial_effective_none_defaults_to_weight(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)], initial_effective={"A": None})
        item_a = [x for x in rr.items if x.key == "A"][0]
        self.assertEqual(item_a.effective_weight, 5)

    def test_smooth_stateful_reset_unknown_key(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        with self.assertRaises(KeyError):
            rr.reset("missing")

    def test_smooth_stateful_disable_and_enable(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1), ("C", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]

        rr.disable("A")
        self.assertEqual(item_a.effective_weight, 0)
        self.assertEqual(rr(), "B")
        self.assertEqual(item_a.effective_weight, 0)

        rr.enable("A")
        self.assertEqual(item_a.effective_weight, 5)  # defaults to full weight
        rr()
        self.assertEqual(item_a.effective_weight, 5)

    def test_smooth_stateful_enable_scales_current_weight(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        item_a.current_weight = 50
        rr.enable("A", effective_weight=1)
        self.assertEqual(item_a.effective_weight, 1)
        self.assertEqual(item_a.current_weight, 10)

    def test_smooth_stateful_disable_no_scale_when_zero(self):
        rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]
        rr.set("A", effective=0)
        item_a.current_weight = 10
        rr.disable("A")
        self.assertEqual(item_a.current_weight, 10)

    def test_smooth_stateful_all_disabled_returns_none(self):
        rr = roundrobin.smooth_stateful([("A", 1), ("B", 1)])
        rr.disable("A")
        rr.disable("B")
        self.assertIsNone(rr())

    def test_smooth_stateful_disable_skips_stale_current_weight(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        item_a = [x for x in rr.items if x.key == "A"][0]

        rr.disable("A")
        self.assertEqual(item_a.effective_weight, 0)

        # Simulate already-accumulated `current_weight` from prior traffic.
        item_a.current_weight = 999
        self.assertEqual(rr(), "B")

    def test_smooth_stateful_disable_unknown_key(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        with self.assertRaises(KeyError):
            rr.disable("missing")

    def test_smooth_stateful_enable_unknown_key(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)])
        with self.assertRaises(KeyError):
            rr.enable("missing")

    def test_smooth_stateful_callable_initial_effective(self):
        rr = roundrobin.smooth_stateful(
            [("A", 5), ("B", 1), ("C", 1)],
            initial_effective=lambda key, weight: 0 if key == "A" else weight,
        )
        result = ''.join([rr() for _ in range(7)])
        self.assertEqual(result, 'BCAABAA')

    def test_smooth_stateful_int_initial_effective_clamps(self):
        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)], initial_effective=999)
        item_a = [x for x in rr.items if x.key == "A"][0]
        item_b = [x for x in rr.items if x.key == "B"][0]
        self.assertEqual(item_a.effective_weight, 5)
        self.assertEqual(item_b.effective_weight, 1)

        rr = roundrobin.smooth_stateful([("A", 5), ("B", 1)], initial_effective=-1)
        item_a = [x for x in rr.items if x.key == "A"][0]
        item_b = [x for x in rr.items if x.key == "B"][0]
        self.assertEqual(item_a.effective_weight, 0)
        self.assertEqual(item_b.effective_weight, 0)

    def test_weighted_not_smooth(self):
        data = [("A", 5), ("B", 1), ("C", 1)]
        get_next = roundrobin.weighted(data)
        result = ''.join([get_next() for _ in range(7)])
        self.assertEqual(result, 'AAAAABC')

    def test_weighted(self):
        data = [("A", 50), ("B", 35), ("C", 15)]
        get_next = roundrobin.weighted(data)

        cnt = {}
        for _ in range(100):
            key = get_next()
            cnt[key] = cnt.get(key, 0) + 1
        self.assertTrue(cnt['A'] == 50)
        self.assertTrue(cnt['B'] == 35)
        self.assertTrue(cnt['C'] == 15)

        cnt = {}
        for _ in range(200):
            key = get_next()
            cnt[key] = cnt.get(key, 0) + 1
        self.assertTrue(cnt['A'] == 100)
        self.assertTrue(cnt['B'] == 70)
        self.assertTrue(cnt['C'] == 30)


if __name__ == "__main__":
    unittest.main()
