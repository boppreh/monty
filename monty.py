import sys
import random
from collections import Counter

class Distribution:
    """
    Class representing a distribution of possible values. Example:

        Distribution(
            (0.495, 'Heads'),
            (0.495, 'Tails'),
            (0.01, 'Sideways'),
        )
    """
    def __init__(self, *pairs):
        result = []
        total = 0
        for probability, value in pairs:
            if probability == 1: probability = 1 - total
            total += probability

            if isinstance(value, Distribution):
                for sub_probability, sub_value in value.pairs:
                    result.append((probability*sub_probability, sub_value))
            else:
                result.append((probability, value))

        self.pairs = tuple(result)

    def generate(self):
        """
        Given a (potentially nested) distribution, generates infniite random
        instances drawn from this distribution.
        """
        total = 0
        running = []
        for probability, value in self.pairs:
            total += probability
            running.append((total, value))
        if total < 1:
            if 1 - total < sys.float_info.epsilon:
                # Compensate for floating point innacuracies.
                running[-1] = (1, running[-1][1])
            else:
                raise ValueError('Incomplete distribution. Total probability is just {:%}.'.format(total))
        while True:
            choice = random.random()
            yield next(value for r, value in running if r >= choice)

    def plot(self, title=None):
        """
        Prints a horizontal bar plot of values in the given distribution.
        """
        if title is not None:
            print(title)
        for prob, value in sorted(self.pairs, reverse=True):
            bar = '['+(round(prob * 40) * '=').ljust(40)+']'
            print('{:>29} {} {:>7.2%}'.format(str(value), bar, prob))
        print('')
        return self

    def join(self, *rest):
        """
        Joins many (potientially nested) distributions into a single flat
        distribution containing all possible combinations, with associated
        probability.
        """
        if len(rest) == 1:
            d2, = rest
        else:
            d2 = rest[0].join(*rest[1:])
        return Distribution(*((p1*p2, (v1, v2)) for p1, v1 in self.pairs for p2, v2 in d2.pairs))
    __add__ = join

    def __mul__(self, n):
        assert int(n) == n and n > 0
        if n == 1:
            return self
        else:
            return self.join(*[self]*(n-1))

    def monte_carlo(self, fn=lambda c: c, n=100000):
        """
        Given a distribution and a function to process lists of examples, returns
        the distribution of processed examples.
        """
        examples = self.generate()
        counter = Counter(fn(next(examples) for i in range(n)))
        total = sum(counter.values()) # Note that `fn` may change the number of examples.
        return Distribution(*((count/total, value) for value, count in counter.most_common()))

    def nest(self, fn):
        """
        Replaces every value with a sub-distribution given by `fn(value)`.
        `fn` may return a Distribution (or Uniform) instance, or simply a
        list of (probability, value) pairs. Returns the flattened
        aggregated distribution.
        """
        counter = Counter()
        for probability, value in self.pairs:
            result = fn(value)
            # Allows for e.g. fn=lambda e: Uniform(e, e+1, e+2) and
            # automatically processes remaining/1 probabilities.
            for sub_probability, sub_value in Distribution(*result):
                counter[sub_value] += sub_probability * probability
        scale = 1/sum(counter.values())
        return Distribution(*((p*scale, v) for v, p in counter.most_common()))
    replace = sub = nest

    def filter(self, fn=lambda c: c):
        """
        Returns a distribution made of only the items that passed the given
        filter. If `fn` returns a number, this is taken as the new probability
        of that value, and the total distribution is updated as such.
        """
        def helper(e):
            result = fn(e)
            return [(float(result), e)] if result else []
        return self.nest(helper)
    update = filter

    def map(self, fn):
        """
        Applies a function to each value in this distribution, then returns the
        distribution of the aggregated results.
        """
        return self.nest(lambda e: [(1, fn(e))])
    group = group_by = map

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
        super().__init__(*((1/len(items), item) for item in items))

D = Distribution
U = Uniform

if __name__ == '__main__':
    # Breast cancer
    # -------------
    # Taken from https://betterexplained.com/articles/an-intuitive-and-short-explanation-of-bayes-theorem/ :
    # 80% of mammograms detect breast cancer when it is there.
    # 9.6% of mammograms detect breast cancer when it’s not there.
    mammogram = lambda status: 0.8 if status == 'Cancer' else 0.096
    # 1% of candidates have breast cancer. What's the likelihood in case of
    # positive mammogram?
    Distribution((0.01, 'Cancer'), (1, 'No cancer')).filter(mammogram).plot()
    #                No cancer [=====================================   ]  92.24%
    #                   Cancer [===                                     ]   7.76%

    # Alternative solution: model the test results in the distribution itself.
    # Note that probabilities are taken in order, so 1 is interpreted as "all
    # remaining probability in this group".
    Distribution(
        # Cancer.
        (0.01, Distribution(
            (0.8, 'True positive'),
            (1,   'False negative')
        )),
        # No cancer.
        (1, Distribution(
            (0.096, 'False positive'),
            (1,     'True negative')
        ))
    ).filter(lambda e: 'positive' in e).plot()
    # If the test was positive, what's the likelihood of having cancer?
    #           False positive [=====================================   ]  92.24%
    #            True positive [===                                     ]   7.76%


    # Waiting at the bus stop
    # -----------------------
    # From https://www.gwern.net/docs/statistics/1994-falk#standard-problems-and-their-solution
    # It's 23:30, you are at the bus stop. Buses usually run at an interval of
    # 30 minutes, but you are only 60% sure they are operating at all at this
    # time.
    bus_distribution = Distribution(
        (0.6, Uniform(
            'Will arrive at 23:35',
            'Will arrive at 23:40',
            'Will arrive at 23:45',
            'Will arrive at 23:50',
            'Will arrive at 23:55',
            'Will arrive at 00:00',
        )),
        (1, 'Not operating'),
    )
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
    # Same setup as classic Monty Hall, now with host opens door 2 or 3 at
    # random.
    opened_doors = Uniform(2, 3)
    # But we only look at situations where opened door *just happened* to not
    # be the car door.
    game = (car_positions + opened_doors).filter(lambda s: s[0] != s[1])
    # What are the strategy likelihoods for winning then?
    game.map(best_strategy).plot()
    #            Switching wins [====================                    ]  50.00%
    #              Staying wins [====================                    ]  50.00%


    # Throw two dice
    # --------------
    # From http://www.mathteacherctk.com/blog/2013/01/13/a-pair-of-probability-games-for-beginners/
    # I win if the difference is 0,1,2. You win if it is 3,4,5. Wanna play?
    dice = Uniform(*range(1, 7))
    (dice * 2).map(lambda pair: 'No' if abs(pair[0]-pair[1])<=2 else 'Yes').plot()
    #                       No [===========================             ]  66.67%
    #                      Yes [=============                           ]  33.33%

    # I win if a 2 or a 5 shows on either die. (Not a sum of 2 or 5, just an
    # occurrence of a 2 or a 5.) Otherwise, you win. Wanna play?
    (dice * 2).map(lambda pair: 'No' if set(pair) & set((2, 5)) else 'Yes').plot()
    #                       No [======================                  ]  55.56%
    #                      Yes [==================                      ]  44.44%