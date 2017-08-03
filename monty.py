import sys
import random
import itertools
from collections import Counter

REST = {}

def join(*ds):
    """
    Joins many (potientially nested) distributions into a single flat
    distribution containing all possible combinations, with associated
    probability.
    """
    result = []
    for pairs in itertools.product(*ds):
        total_p = 1
        value = []
        for v, p in pairs:
            total_p *= p
            value.append(v)
        result.append((tuple(value), total_p))
    return Distribution(*result)

class Distribution:
    """
    Class representing a distribution of possible values. Example:

        Distribution(
            (0.495, 'Heads'),
            (0.495, 'Tails'),
            (0.01, 'Sideways'),
        )
    """
    def __init__(self, *args, **kwargs):
        if kwargs:
            # Distribution(a=0.5, b=0.1, c=REST)
            assert not args
            args = [kwargs]
        if len(args) == 1 and isinstance(args[0], dict):
            # Distribution({'a': 0.5, 'b': 0.1, 'c': REST})
            args = args[0].items()

        pairs_list = []
        self.total = 0
        for value, probability in args:
            if probability is REST:
                probability = 1 - self.total

            if isinstance(value, Distribution):
                for sub_value, sub_probability in value.normalized():
                    pairs_list.append((sub_value, probability*sub_probability))
                    self.total += probability*sub_probability
            else:
                pairs_list.append((value, probability))
                self.total += probability

        self.pairs = tuple(pairs_list)

    def normalized(self):
        return Distribution(*((v, p/self.total) for v, p in self))

    def generate(self, n=-1):
        """
        Given a (potentially nested) distribution, generates infniite random
        instances drawn from this distribution. If `n` is given, the only `n`
        are generated.
        """
        total = 0
        running = []
        for value, probability in self.normalized():
            total += probability
            running.append((value, total))

        if total < 1:
            if 1 - total < sys.float_info.epsilon:
                # Compensate for floating point innacuracies.
                running[-1] = (running[-1][1], 1)
            else:
                raise ValueError('Incomplete distribution. Total probability is just {:%}.'.format(total))

        while n != 0:
            choice = random.random()
            yield next(value for value, r in running if r >= choice)
            n -= 1

    def plot(self, title=None):
        """
        Prints a horizontal bar plot of values in the given distribution.
        """
        if title is not None:
            print(title)

        counter = Counter()
        for v, p in self.normalized():
            counter[str(v)] += p

        for str_value, prob in counter.most_common():
            bar = '['+(round(prob * 40) * '=').ljust(40)+']'
            # 29 is used to make the whole line be 80 characters, ensuring
            # every plot is aligned with every other plot.
            print('{:>29} {:>7.2%} {}'.format(str_value, prob, bar))
        print('')
        return self

    def __mul__(self, n):
        return join(*[self]*n)
    __rmul__ = __mul__

    def monte_carlo(self, fn=lambda c: c, n=100000):
        """
        Given a distribution and a function to process lists of examples, returns
        the distribution of processed examples.
        """
        examples = self.generate()
        counter = Counter(fn(next(examples) for i in range(n)))
        scale = 1/sum(counter.values()) # Note that `fn` may change the number of examples.
        return Distribution(*((value, count*scale) for value, count in counter.most_common()))

    def _nest(self, fn):
        """
        Replaces every value with a sub-distribution given by `fn(value)`.
        `fn` may return a Distribution (or Uniform) instance, or simply a
        list of (probability, value) pairs. Returns the flattened
        aggregated distribution.
        """
        if isinstance(fn, dict): fn = fn.__getitem__
        counter = Counter()
        for value, probability in self:
            for sub_value, sub_probability in fn(value):
                counter[sub_value] += sub_probability * probability
        return Distribution(*counter.most_common())

    def filter(self, fn=None, **kwargs):
        """
        Returns a distribution made of only the items that passed the given
        filter. If `fn` returns a number, this is taken as the new probability
        of that value, and the total distribution is updated as such.

        `fn` can also be a dictionary mapping values to results, or a list,
        so that only items in the list will be selected.
        """
        if kwargs:
            assert fn is None
            fn = kwargs.__getitem__
        elif fn is None:
            fn = lambda c: c
        elif isinstance(fn, dict):
            fn = fn.__getitem__
        elif not callable(fn):
            fn = fn.__contains__
        def helper(e):
            result = fn(e)
            return [(e, float(result))] if result else []
        return self._nest(helper)
    update = filter

    def map(self, fn):
        """
        Applies a function to each value in this distribution, then returns the
        distribution of the aggregated results.

        `fn` can also be a dictionary, mapping values to their replacements.
        """
        if not callable(fn): fn = fn.__getitem__
        return self._nest(lambda e: Distribution((fn(e), 1)))
    group = group_by = map

    def opposite(self):
        """
        Returns a distribution with the opposite odds for each item, already
        normalized.
        """
        opposite_pairs = [(v, 1-p) for p, v in self]
        scale = 1/sum(p for v, p in opposite_pairs)
        return Distribution(*((v, scale*p) for v, p in opposite_pairs))
    __neg__ = opposite

    def utility(self, utility_function=lambda v: v):
        return sum(p * utility_function(v) for v, p in self)

    def __repr__(self):
        return repr(self.pairs)

    def __iter__(self):
        return iter(self.pairs)

    def __hash__(self):
        return hash(self.pairs)

    def __eq__(self, other):
        return isinstance(other, Distribution) and self.pairs == other.pairs

class Uniform(Distribution):
    """
    Class representing an uniform distribution of possible values. Example:

        Uniform('Heads', 'Tails', 'Sideways') == Distribution(
            (0.333, 'Heads'),
            (0.333, 'Tails'),
            (0.333, 'Sideways'),
        )
    """
    def __init__(self, *items):
        super().__init__(*((item, 1/len(items)) for item in items))

class Fixed(Distribution):
    def __init__(self, item):
        super().__init__((item, 1))
class Range(Uniform):
    def __init__(self, a, b=None):
        super().__init__(*range(a, b))
class Count(Uniform):
    def __init__(self, a, b=None):
        if b is None:
            a, b = 1, a
        super().__init__(*range(a, b+1))
class Permutations(Uniform):
    def __init__(self, *items):
        super().__init__(*itertools.permutations(items))

# Shorthand.
D = Distribution
U = Uniform
R = Range
C = Count
F = Fixed

# Common discrete distributions used in examples.
coin = Uniform('Heads', 'Tails')
dice = die = d6 = Count(6)
d4 = Count(4)
d8 = Count(8)
d10 = Count(10)
d12 = Count(12)
d20 = Count(20)
d100 = Count(100)
card_ranks = Uniform('Ace', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'Jack', 'Queen', 'King')
card_suits = Uniform('Clubs', 'Diamonds', 'Hearts', 'Spades')
deck = join(card_ranks, card_suits)
rock_paper_scissors = Uniform('Rock', 'Paper', 'Scissors')
monty_hall_doors = Permutations('Goat', 'Goat', 'Car')

# Common filters and maps.
import operator
lt = lambda s: operator.lt(*s)
le = lambda s: operator.le(*s)
eq = equal = equals = lambda s: operator.eq(*s)
ne = not_equal = not_equals = lambda s: operator.ne(*s)
gt = lambda s: operator.gt(*s)
ge = lambda s: operator.ge(*s)
contains = lambda s: operator.contains(*s)

add = sum
sub = lambda s: operator.lt(*s)
difference = lambda s: abs(s[0]-s[1])
from functools import reduce
mul = product = lambda s: reduce(operator.mul, s)

first = lambda s: s[0]
second = lambda s: s[1]
third = lambda s: s[2]
last = lambda s: s[-1]

class Volume(Distribution):
    """
    Uses the Distribution algorithms to model concentration of solutions.
    "Probabilities" are treated as volumes and therefore not normalized.
    Also overrides arithmetic operators to behave like mixing liquids. Example:

        juice = Volume(water=200, orange=600)
        sugar_water = Volume(water=95, sugar=5)
        juice + sugar_water/2 # total volume: (200+600 + (95+5)/2) = 850
        Volume({juice: 1, sugar_water: 1}) # Mix 1-1, total volume: 1.0, 2.5% sugar
    """
    def __add__(self, other):
        counter = Counter()
        for v, p in self: counter[v] += p
        for v, p in other: counter[v] += p
        return Volume(*counter.most_common())
    def __mul__(self, n):
        return Volume(*((v, p*n) for v, p in self))
    __rmul__ = __mul__
    def __div__(self, n):
        return self * (1/n)
    __truediv__ = __div__


if __name__ == '__main__':
    # Breast cancer
    # -------------
    # Taken from https://betterexplained.com/articles/an-intuitive-and-short-explanation-of-bayes-theorem/ :
    # 80% of mammograms detect breast cancer when it is there.
    # 9.6% of mammograms detect breast cancer when it’s not there.
    positive_mammogram = {'Cancer': 0.8, 'No cancer': 0.096}
    # 1% of candidates have breast cancer. What's the likelihood after a
    # positive test?
    Distribution({'Cancer': 0.01, 'No cancer': REST}).filter(positive_mammogram).plot()
    #                No cancer [=====================================   ]  92.24%
    #                   Cancer [===                                     ]   7.76%

    # Alternative solution: model the test results in the distribution itself.
    Distribution({
        # Cancer.
        Distribution({'True positive': 0.8, 'False negative': REST}): 0.01,
        # No cancer.
        Distribution({'False positive': 0.096, 'True negative': REST}): REST,
    }).filter(['True positive', 'False positive']).plot()
    # If the test was positive, what's the likelihood of having cancer?
    #           False positive [=====================================   ]  92.24%
    #            True positive [===                                     ]   7.76%


    # Waiting at the bus stop
    # -----------------------
    # From https://www.gwern.net/docs/statistics/1994-falk#standard-problems-and-their-solution
    # It's 23:30, you are at the bus stop. Buses usually run at an interval of
    # 30 minutes, but you are only 60% sure they are operating at all at this
    # time.
    bus_distribution = Distribution({
        Uniform(
            'Will arrive at 23:35',
            'Will arrive at 23:40',
            'Will arrive at 23:45',
            'Will arrive at 23:50',
            'Will arrive at 23:55',
            'Will arrive at 00:00',
        ): 0.6,
        'Not operating': REST,
    })
    # 5 minutes pass. It's now 23:35, and the bus has not yet arrived. What
    # are the new likelihoods?
    bus_distribution.filter(lambda e: '23:35' not in e).plot()
    #            Not operating [==================                      ]  44.44%
    #     Will arrive at 23:55 [====                                    ]  11.11%
    #     Will arrive at 23:50 [====                                    ]  11.11%
    #     Will arrive at 23:45 [====                                    ]  11.11%
    #     Will arrive at 23:40 [====                                    ]  11.11%
    #     Will arrive at 00:00 [====                                    ]  11.11%

    # It's now 23:55, and the bus has not yet arrived.
    bus_distribution.filter(lambda e: '23:' not in e).plot()
    #            Not operating [================================        ]  80.00%
    #     Will arrive at 00:00 [========                                ]  20.00%


    # Monty Hall problem
    # ------------------
    # A car is put behind one of three doors.
    car_positions = Uniform(1, 2, 3)

    def open_door(car_position):
        # The host opens one of the other doors that does not contain the car.
        opened_door = {1: random.choice([2, 3]), 2: 3, 3: 2}[car_position]
        return (car_position, opened_door)

    def best_strategy(state):
        car_position, opened_door = state

        # The participant starts selecting door number 1.
        # Seeing the empty door, the participant may choose to switch.
        switched = {2: 3, 3: 2}[opened_door]

        # For *this* game, which strategy wins?
        return 'Switching wins' if switched == car_position else 'Staying wins'

        # Note that because only two doors remain, and the strategies are
        # always opposites, you can negate the final condition and simplify
        # to just "return 'stay' if car_position == 1 else 'switch'".
        # But if you realise this, the result becomes trivial.

    # Compute the total likelihood of each strategy winning.
    car_positions.map(open_door).map(best_strategy).plot()
    #           Switching wins [===========================             ]  66.67%
    #             Staying wins [=============                           ]  33.33%


    # Monty Hall - Ignorant Monty version
    # -----------------------------------
    # Same setup as classic Monty Hall, now with host opening door 2 or 3 at
    # random.
    opened_doors = Uniform(2, 3)
    # But we only look at situations where the opened door *just happened* to
    # not be the car door.
    game = join(car_positions, opened_doors).filter(not_equals)
    # What are the strategy likelihoods for winning then?
    game.map(best_strategy).plot()
    #            Switching wins [====================                    ]  50.00%
    #              Staying wins [====================                    ]  50.00%


    # Throw two dice
    # --------------
    # From http://www.mathteacherctk.com/blog/2013/01/13/a-pair-of-probability-games-for-beginners/
    # Throw two dice. I win if the difference is 0,1,2. You win if it is 3,4,5.
    # Wanna play?
    (2*dice).map(difference).map(lambda d: 'No' if d <= 2 else 'Yes').plot()
    #                       No [===========================             ]  66.67%
    #                      Yes [=============                           ]  33.33%

    # I win if a 2 or a 5 shows on either die. (Not a sum of 2 or 5, just an
    # occurrence of a 2 or a 5.) Otherwise, you win. Wanna play?
    (2*dice).map(lambda pair: 'No' if 2 in pair or 5 in pair else 'Yes').plot()
    #                       No [======================                  ]  55.56%
    #                      Yes [==================                      ]  44.44%


    # Unbiased flip from biased coin
    # ------------------------------
    # From John von Neuman (1951)

    # I want a fair coin flip, but I don't trust this coin. Can I "unbias" it?
    b_coin = Distribution(Heads=0.6, Tails=REST)

    # Yes! Flip it twice, and retry until they are different. Then look at
    # the first one.
    (2*b_coin).filter(not_equals).map(first).plot()
    #                    Tails  50.00% [====================                    ]
    #                    Heads  50.00% [====================                    ]

    # Mixing solutions
    # ----------------

    # You can also use probability distributions to keep track of
    # concentrations in solutions.

    # 200 units of water and 600 units of pure orange.
    juice = Volume(water=200, orange=600).plot()
    #                   orange  75.00% [==============================          ]
    #                    water  25.00% [==========                              ]

    # 100 units of sugar water at 5%
    sugar_water = Volume(water=95, sugar=5).plot()
    #                    water  95.00% [======================================  ]
    #                    sugar   5.00% [==                                      ]

    # Mix all of the juice with half of the sugar water.
    mix = (juice + sugar_water/2).plot()
    #                   orange  70.59% [============================            ]
    #                    water  29.12% [============                            ]
    #                    sugar   0.29% [                                        ]

    # Remove most of the orange and some of the sugar.
    filtered = mix.filter(water=1, orange=0.01, sugar=0.80).plot()
    #                    water  96.87% [======================================= ]
    #                   orange   2.35% [=                                       ]
    #                    sugar   0.78% [                                        ]
    print(filtered, filtered.total)
    # (('water', 247.5), ('orange', 6.0), ('sugar', 2.0)) 255.5

    # Mix 1 units of juice and sugar water at 50/50, resulting in 2.5% sugar.
    Volume({juice: 1, sugar_water: 1}).plot()
    #                    water  60.00% [========================                ]
    #                   orange  37.50% [===============                         ]
    #                    sugar   2.50% [=                                       ]


    # Is the coin biased?
    # -------------------


    # Makeshift dice
    # --------------
    # I need a D20 roll, but all I have are D4. Can I just add 5xD4?
    d20.plot()
    #                        1   5.00% [==                                      ]
    #                        2   5.00% [==                                      ]
    #                        3   5.00% [==                                      ]
    #                        4   5.00% [==                                      ]
    #                        5   5.00% [==                                      ]
    #                        6   5.00% [==                                      ]
    #                        7   5.00% [==                                      ]
    #                        8   5.00% [==                                      ]
    #                        9   5.00% [==                                      ]
    #                       10   5.00% [==                                      ]
    #                       11   5.00% [==                                      ]
    #                       12   5.00% [==                                      ]
    #                       13   5.00% [==                                      ]
    #                       14   5.00% [==                                      ]
    #                       15   5.00% [==                                      ]
    #                       16   5.00% [==                                      ]
    #                       17   5.00% [==                                      ]
    #                       18   5.00% [==                                      ]
    #                       19   5.00% [==                                      ]
    #                       20   5.00% [==                                      ]
    (5 * d4).map(sum).plot()
    #                       12  15.14% [======                                  ]
    #                       13  15.14% [======                                  ]
    #                       11  13.18% [=====                                   ]
    #                       14  13.18% [=====                                   ]
    #                       10   9.86% [====                                    ]
    #                       15   9.86% [====                                    ]
    #                        9   6.35% [===                                     ]
    #                       16   6.35% [===                                     ]
    #                        8   3.42% [=                                       ]
    #                       17   3.42% [=                                       ]
    #                        7   1.46% [=                                       ]
    #                       18   1.46% [=                                       ]
    #                        6   0.49% [                                        ]
    #                       19   0.49% [                                        ]
    #                        5   0.10% [                                        ]
    #                       20   0.10% [                                        ]
    # Nope.


    # Dungeons and confused dragons
    # -----------------------------
    # Roll a D20, a D12 and a D4. What's the probability of the D20 and the D12
    # being less than the D4 away from each other?
    join(d20, d12, d4).map(lambda s: abs(s[0]-s[1]) < s[2]).plot()
    #                    False  81.04% [================================        ]
    #                     True  18.96% [========                                ]


    # Daughters
    # ---------
    # If a family has two children...
    children = Uniform('Son', 'Daughter') * 2

    # ... at least one of which is a daughter, what is the probability that
    # both of them are daughters?
    children.filter(lambda s: 'Daughter' in s).map(eq).plot()
    #                    False  66.67% [===========================             ]
    #                     True  33.33% [=============                           ]

    # ... the elder of which is a daughter, what is the probability that both
    # of them are the daughters?
    children.filter(lambda s: s[1] == 'Daughter').map(eq).plot()
    #                    False  50.00% [====================                    ]
    #                     True  50.00% [====================                    ]


    # Non transitive dice
    # -------------------
    dice_a = Uniform(2, 2, 4, 4, 9, 9)
    dice_b = Uniform(1, 1, 6, 6, 8, 8)
    dice_c = Uniform(3, 3, 5, 5, 7, 7)

    join(dice_a, dice_b).map(gt).map(['A wins', 'B wins']).plot()
    #                   B wins  55.56% [======================                  ]
    #                   A wins  44.44% [==================                      ]

    join(dice_b, dice_c).map(gt).map(['B wins', 'C wins']).plot()
    #                   C wins  55.56% [======================                  ]
    #                   B wins  44.44% [==================                      ]

    join(dice_c, dice_a).map(gt).map(['C wins', 'A wins']).plot()
    #                   A wins  55.56% [======================                  ]
    #                   C wins  44.44% [==================                      ]


    # Sleeping beauty
    # ---------------
    # Today is Sunday. Sleeping Beauty drinks a powerful sleeping potion and
    # falls asleep. Her attendant tosses a fair coin and records the result.

    # - The coin lands in Heads. Beauty is awakened only on Monday and
    # interviewed. Her memory is erased and she is again put back to sleep.

    # - The coin lands in Tails. Beauty is awakened and interviewed on Monday.
    # Her memory is erased and she's put back to sleep again. On Tuesday, she is
    # once again awaken, interviewed and finally put back to sleep.

    # The most important question she's asked in the interviews is
    # "What is your credence (degree of belief) that the coin landed in heads?""

    days = join(coin, Uniform('Monday', 'Tuesday'))

    def add_guess(state):
        if state == ('Heads', 'Tuesday'):
            # Sleeping beauty is not awakened in this case.
            return Uniform()
        else:
            # She tries to guess the coin toss.
            return Uniform(state+('Heads',), state+('Tails',))
    guesses = days.map(add_guess).plot()
    #  ('Heads', 'Monday', 'Heads')  16.67% [=======                                 ]
    #  ('Heads', 'Monday', 'Tails')  16.67% [=======                                 ]
    #  ('Tails', 'Monday', 'Heads')  16.67% [=======                                 ]
    #  ('Tails', 'Monday', 'Tails')  16.67% [=======                                 ]
    # ('Tails', 'Tuesday', 'Heads')  16.67% [=======                                 ]
    # ('Tails', 'Tuesday', 'Tails')  16.67% [=======                                 ]

    def verify_guess(state):
        actual, day, guess = state
        if actual == guess:
            return 'Correct ' + guess
        else:
            return 'Incorrect'
    guesses.map(verify_guess).plot()
    #                Incorrect  50.00% [====================                    ]
    #            Correct Tails  33.33% [=============                           ]
    #            Correct Heads  16.67% [=======                                 ]

    # She is right more often by guessing tails. But no event gave her any
    # evidence. Should she believe the coin landed tails?


    # Ellsberg Paradox
    # ----------------
    # (simplified here to uniform distribution)

    # In an urn, you have 9 balls of 3 colors: red, blue and yellow. 3 balls
    # are known to be red. All the other balls are either blue or yellow.

    red = Fixed('Red')
    either = Uniform('Blue', 'Yellow')
    urn = join(red, red, red, either, either, either, either, either, either)

    random_ball = urn.map(lambda s: Uniform(*s))

    # There are two lotteries:
    # Lottery A: A random ball is chosen. You win a prize if the ball is red.
    # Lottery B: A random ball is chosen. You win a prize if the ball is blue.
    # Question: In which lottery would you want to participate?
    random_ball.map({
        'Red': 'Lottery A',
        'Blue': 'Lottery B',
        'Yellow': 'N/A',
    }).plot()
    #                Lottery A  33.33% [=============                           ]
    #                Lottery B  33.33% [=============                           ]
    #                      N/A  33.33% [=============                           ]

    # Lottery X: A random ball is chosen. You win a prize if the ball is either red or yellow.
    # Lottery Y: A random ball is chosen. You win a prize if the ball is either blue or yellow.
    # Question: In which lottery would you want to participate?
    random_ball.map({
        'Red': 'Lottery A',
        'Blue': 'Lottery B',
        'Yellow': Uniform('Lottery A', 'Lottery B'),
    }).plot()
    #                Lottery A  50.00% [====================                    ]
    #                Lottery B  50.00% [====================                    ]