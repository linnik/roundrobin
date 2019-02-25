import unittest

import roundrobin


class WeightCase(unittest.TestCase):

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
