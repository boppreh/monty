import io
from contextlib import redirect_stdout
from replace_me import hardcode_me
import unittest
from monty import *

class TestConstruction(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(list(Distribution()), [])

    def test_list_pairs(self):
        d = Distribution([('a', 0.5), ('b', 0.1), ('c', REST)])
        self.assertEqual(list(d), [('a', 0.5), ('b', 0.1), ('c', 0.4)])

    def test_dictionary(self):
        d = Distribution({'a': 0.5, 'b': 0.1, 'c': REST})
        self.assertEqual(list(d), [('a', 0.5), ('b', 0.1), ('c', 0.4)])

    def test_kwargs(self):
        d = Distribution(a=0.5, b=0.1, c=REST)
        self.assertEqual(list(d), [('a', 0.5), ('b', 0.1), ('c', 0.4)])

    def test_improper_rest_position(self):
        with self.assertRaises(ValueError):
            Distribution([('a', 0.5), ('b', REST), ('c', 0.4)])

    def test_improper_rest_value(self):
        with self.assertRaises(ValueError):
            Distribution([('a', 10), ('b', REST), ('c', 0)])

    def test_improper_odds(self):
        with self.assertRaises(ValueError):
            Distribution([('a', 10), ('b', -1)])

    def test_odds(self):
        d = Distribution([('a', 5), ('b', 1), ('c', 4)])
        self.assertEqual(list(d), [('a', 5), ('b', 1), ('c', 4)])

    def test_sub_distribution(self):
        d = Distribution([('a', 40), (Distribution(b=5, c=5), 20)])
        self.assertEqual(list(d), [('a', 40), ('b', 10), ('c', 10)])

    def test_sub_distribution_not_flatten(self):
        d = Distribution([('a', 40), (Distribution(b=5, c=5), 20)], force_flatten=False)
        self.assertEqual(list(d), [('a', 40), (Distribution(b=5, c=5), 20)])

    def test_merge(self):
        d = Distribution(('a', 10), ('b', 5), ('a', 5))
        self.assertEqual(list(d), [('a', 15), ('b', 5)])

    def test_not_merge(self):
        d = Distribution(('a', 10), ('b', 5), ('a', 5), force_merge=False)
        self.assertEqual(list(d), [('a', 10), ('b', 5), ('a', 5)])

    def test_non_hashable(self):
        a = list()
        self.assertEqual(list(Distribution((a, 1), force_merge=False)), [(a, 1)])

class TestGet(unittest.TestCase):
    def test_missing_empty(self):
        with self.assertRaises(KeyError):
            Distribution()['missing']

    def test_missing(self):
        with self.assertRaises(KeyError):
            Distribution(A=5, B=10)['missing']

    def test_first(self):
        self.assertEqual(Distribution(A=5, B=10)['A'], 5)

    def test_last(self):
        self.assertEqual(Distribution(A=5, B=10)['B'], 10)

    def test_duplicated(self):
        self.assertEqual(Distribution(('a', 5), ('b', 10), ('a', 15), force_merge=False)['a'], 5)

class TestNormalize(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(list(Distribution().normalize()), [])

    def test_one_correct(self):
        self.assertEqual(list(Distribution(A=1).normalize()), [('A', 1)])

    def test_one_normalize(self):
        self.assertEqual(list(Distribution(A=10).normalize()), [('A', 1)])

    def test_one_zero(self):
        self.assertEqual(list(Distribution(A=0).normalize()), [('A', 0)])

    def test_many_correct(self):
        self.assertEqual(list(Distribution(A=0.7, B=0.3).normalize()), [('A', 0.7), ('B', 0.3)])

    def test_many_normalize(self):
        self.assertEqual(list(Distribution(A=7, B=3).normalize()), [('A', 0.7), ('B', 0.3)])

    def test_keep_nesting(self):
        d = Distribution((Distribution(A=5, B=10), 1), force_flatten=False)
        self.assertEqual(list(d.normalize()), [(Distribution(A=5, B=10), 1)])

    def test_keep_duplicates(self):
        d = Distribution(('a', 1), ('a', 4), force_merge=False)
        self.assertEqual(list(d.normalize()), [('a', 0.2), ('a', 0.8)])

class TestGenerate(unittest.TestCase):
    def test_empty(self):
        with self.assertRaises(ValueError):
            list(Distribution().generate(1))

    def test_zero_empty(self):
        self.assertEqual(list(Distribution().generate(0)), [])

    def test_zero(self):
        self.assertEqual(list(Distribution(a=5).generate(0)), [])

    def test_single(self):
        self.assertTrue(all(v == 'A' for v in Distribution(A=0.1).generate(10)))

    def test_count(self):
        self.assertEqual(len(list(Distribution(A=0.1).generate(10))), 10)

    def test_multiple(self):
        self.assertTrue(all(v in 'AB' for v in Distribution(A=0.1, B=0.9).generate(10)))

    def test_monte_carlo(self):
        def process(gen):
            gen = list(gen)
            self.assertEqual(len(gen), 100)
            self.assertTrue(all(i in 'AB' for i in gen))
            return ['A', 'B', 'C', 'A']
        Distribution(A=1, B=2).monte_carlo(process, n=100)

class TestPlot(unittest.TestCase):
    def test_empty(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution().plot()
        self.assertEqual(f.getvalue(), '\n\n')

    def test_title(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution().plot('Title')
        self.assertEqual(f.getvalue(), 'Title\n\n\n')

    def test_one_normalized(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=1).plot()
        self.assertEqual(f.getvalue(), '\n                            A 100.00% [========================================]\n\n')

    def test_one_not_normalized(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=0.5).plot()
        self.assertEqual(f.getvalue(), '\n                            A 100.00% [========================================]\n\n')

    def test_one_zero_filter(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=0).plot()
        self.assertEqual(f.getvalue(), '\n\n')

    def test_one_zero_not_filter(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=0).plot(filter=False)
        self.assertEqual(f.getvalue(), '\n                            A   0.00% [                                        ]\n\n')

    def test_two_sort(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=1, B=2).plot()
        self.assertEqual(f.getvalue(), '\n                            B  66.67% [===========================             ]\n                            A  33.33% [=============                           ]\n\n') 

    def test_two_not_sort(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution(A=1, B=2).plot(sort=False)
        self.assertEqual(f.getvalue(), '\n                            A  33.33% [=============                           ]\n                            B  66.67% [===========================             ]\n\n')

    def test_non_hashable(self):
        f = io.StringIO()
        with redirect_stdout(f):
            Distribution((list(), 1), force_merge=False).plot()
        self.assertEqual(f.getvalue(), '\n                           [] 100.00% [========================================]\n\n')

class TestJoin(unittest.TestCase):
    def test_one_empty(self):
        self.assertEqual(list(join(Distribution())), [])

    def test_two_empty(self):
        self.assertEqual(list(join(Distribution(), Distribution())), [])

    def test_one(self):
        self.assertEqual(list(join(Distribution(A=5))), [(('A',), 5)])

    def test_two_with_empty(self):
        self.assertEqual(list(join(Distribution(A=5), Distribution())), [])

    def test_two(self):
        j = join(Distribution(A=5, B=10), Distribution(B=5, C=10))
        self.assertEqual(list(j), [(('A', 'B'), 25), (('A', 'C'), 50), (('B', 'B'), 50), (('B', 'C'), 100)])

    def test_multiplication_by_zero(self):
        self.assertEqual(list(Distribution(A=5, B=10)*0), [((), 1)])

    def test_multiplication_by_one(self):
        self.assertEqual(list(Distribution(A=5, B=10)*1), [(('A',), 5), (('B',), 10)])

    def test_multiplication(self):
        self.assertEqual(list(2*Distribution(A=5, B=10)), [(('A', 'A'), 25), (('A', 'B'), 50), (('B', 'A'), 50), (('B', 'B'), 100)])

class TestStatistics(unittest.TestCase):
    def test_expected_value(self):
        self.assertEqual(Distribution((1, 0.5), (2, 0.5)).expected_value, 1.5)

    def test_expected_value_normalize(self):
        self.assertEqual(Distribution((1, 5), (2, 5)).expected_value, 1.5)

    def test_expected_value_empty(self):
        self.assertEqual(Distribution().expected_value, 0)

    def test_mode(self):
        self.assertEqual(Distribution(A=5, B=10, C=5).mode, 'B')

    def test_utility(self):
        self.assertEqual(Distribution(A=5, AA=10, AAA=5).utility(len), 2)

class TestMap(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(Distribution().map(lambda e: e), ())

    def test_fn_function(self):
        self.assertEqual(Distribution(A=5, B=10).map(str.lower), (('a', 5), ('b', 10)))

    def test_fn_none(self):
        self.assertEqual(Distribution(('A', 5), ('', 10)).map(), ((True, 5), (False, 10)))

    def test_fn_dict(self):
        self.assertEqual(Distribution(A=5, B=10).map({'A': 'a', 'B': 'b'}), (('a', 5), ('b', 10)))

    def test_fn_kwargs(self):
        self.assertEqual(Distribution(A=5, B=10).map(A='a', B='b'), (('a', 5), ('b', 10)))

    def test_fn_list(self):
        self.assertEqual(Distribution(A=5, B=10).map(['A']), ((True, 5), (False, 10)))

    def test_starmap(self):
        self.assertEqual(Distribution(((1, 2), 0.7), ((3, 4), 0.3)).starmap(lambda a, b: a+b), ((3, 0.7), (7, 0.3)))

    def test_grouping(self):
        self.assertEqual(Distribution(A=5, a=10).map(str.lower), (('a', 15),))

    def test_sub_distribution(self):
        self.assertEqual(Distribution(A=1).map(A=Distribution(a=2, b=3)), (('a', 0.4), ('b', 0.6)))

    def test_from_unhashable(self):
        d = Distribution(([], 0.5), ([1, 2, 3], 0.5), force_merge=False)
        self.assertEqual(d.map(len), ((0, 0.5), (3, 0.5)))

    def test_to_unhashable(self):
        d = Distribution((0, 0.5), (3, 0.5), force_merge=False)
        self.assertEqual(d.map(lambda i: [1]*i), (([], 0.5), ([1, 1, 1], 0.5)))

class TestFilter(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(Distribution().filter(lambda e: e), ())

    def test_fn_function(self):
        self.assertEqual(Distribution(A=5, BB=10).filter(len), (('A', 5), ('BB', 20)))

    def test_fn_none(self):
        self.assertEqual(Distribution(('A', 5), ('', 10)).filter(), (('A', 5), ('', 0)))

    def test_fn_dict(self):
        self.assertEqual(Distribution(A=5, B=10).filter({'A': 2, 'B': 0.5}), (('A', 10), ('B', 5)))

    def test_fn_kwargs(self):
        self.assertEqual(Distribution(A=5, B=10).filter(A=2, B=0.5), (('A', 10), ('B', 5)))

    def test_fn_list(self):
        self.assertEqual(Distribution(A=5, B=10).filter(['A']), (('A', 5), ('B', 0)))

    def test_starfilter(self):
        self.assertEqual(Distribution(((1, 2), 10), ((3, 4), 20)).starfilter(lambda a, b: a+b), (((1, 2), 30), ((3, 4), 140)))

    def test_from_unhashable(self):
        d = Distribution(([], 0.5), ([1, 2, 3], 0.5), force_merge=False)
        self.assertEqual(d.filter(len), (([], 0.0), ([1, 2, 3], 1.5)))

class TestHelpers(unittest.TestCase):
    def test_uniform_empty(self):
        self.assertEqual(Uniform(), ())

    def test_uniform_one(self):
        self.assertEqual(Uniform(1), ((1, 1),))

    def test_uniform_many(self):
        self.assertEqual(Uniform(1, 2), ((1, 0.5), (2, 0.5)))

    def test_fixed(self):
        self.assertEqual(Fixed(1), ((1, 1),))

    def test_range_implicit(self):
        self.assertEqual(Range(4), ((0, 0.25), (1, 0.25), (2, 0.25), (3, 0.25)))

    def test_range_explicit(self):
        self.assertEqual(Range(2, 4), ((2, 0.5), (3, 0.5)))

    def test_count_implicit(self):
        self.assertEqual(Count(4), ((1, 0.25), (2, 0.25), (3, 0.25), (4, 0.25)))

    def test_count_explicit(self):
        self.assertEqual(Count(3, 4), ((3, 0.5), (4, 0.5)))

class TestSolution(unittest.TestCase):
    def setUp(self):
        self.orange = Solution(Orange=1)
        self.water = Solution(Water=1)
        self.juice = Solution((self.water, 300), (self.orange, 700))

    def test_empty(self):
        self.assertEqual(Solution(), ())

    def test_volume(self):
        self.assertEqual(self.juice, (('Water', 300), ('Orange', 700)))

    def test_add(self):
        self.assertEqual(self.juice+self.juice, (('Water', 600), ('Orange', 1400)))

    def test_mul(self):
        self.assertEqual(self.juice*2, (('Water', 600), ('Orange', 1400)))

    def test_div(self):
        self.assertEqual(self.juice/2, (('Water', 150), ('Orange', 350)))

if __name__  == '__main__':
    unittest.main()
