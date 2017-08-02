import sys
import random
from collections import Counter

def flip(chance=0.5):
    """
    Returns True with probability `chance`.
    flip() = flip(0.5) = fair coin
    flip(0.1) = 10% chance of True
    """
    return random.random() < chance

DEFAULT_N_EXAMPLES = 100000
class Distribution:
    def __init__(self, *pairs):
        self.pairs = []
        for probability, value in pairs:
            if isinstance(value, Distribution):
                for sub_probability, sub_value in value.pairs:
                    self.pairs.append((probability*sub_probability, sub_value))
            else:
                self.pairs.append((probability, value))

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

    def plot(self):
        """
        Prints a horizontal bar plot of values in the given distribution.
        """
        items = [(prob, str(value)) for prob, value in self.pairs]
        longest_key = max(len(value) for prob, value in items)
        for prob, value in sorted(items, reverse=True):
            bar = '['+(round(prob * 40) * '=').ljust(40)+']'
            print(value.rjust(longest_key), bar, '{:>7.2%}'.format(prob))
        print('')

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

    def apply(self, fn=lambda c: c, n=DEFAULT_N_EXAMPLES):
        """
        Given a distribution and a function to process lists of examples, returns
        the distribution of processed examples.
        """
        examples = self.generate()
        counter = Counter(fn(next(examples) for i in range(n)))
        total = sum(counter.values()) # Note that `fn` may change the number of examples.
        return Distribution(*((count/total, value) for value, count in counter.most_common()))

    def filter(self, fn=lambda c: True, n=DEFAULT_N_EXAMPLES):
        return self.apply(lambda e: (c for c in e if fn(c)), n=n)

    def map(self, fn=lambda c: True, n=DEFAULT_N_EXAMPLES):
        return self.apply(lambda e: (fn(c) for c in e), n=n)
D = Distribution

class Uniform(Distribution):
    def __init__(self, *items):
        super().__init__(*((1/len(items), item) for item in items))
U = Uniform

if __name__ == '__main__':
    # Breast cancer
    # -------------
    # Taken from https://betterexplained.com/articles/an-intuitive-and-short-explanation-of-bayes-theorem/ :
    # 1% of candidates have breast cancer.
    cancer_distribution = D((0.01, 'cancer'), (0.99, 'no cancer'))
    def positive_mammogram(status):
        # 80% of mammograms detect breast cancer when it is there.
        # 9.6% of mammograms detect breast cancer when it’s not there.
        return flip(0.8 if status == 'cancer' else 0.096)
    # If the test was positive, what's the likelihood of having cancer?
    cancer_distribution.filter(positive_mammogram).plot()
    # no cancer [=====================================   ]  91.95%
    #    cancer [===                                     ]   8.05%

    # Alternative solution: model the test results in the distribution itself.
    # Note that probabilities are taken in order, so 1 is interpreted as "all
    # remaining probability".
    test_distribution = Distribution(
        # Cancer
        (0.01, Distribution(
            (0.8, 'True positive'),
            (1, 'False negative')
        )),
        # No cancer
        (1, Distribution(
            (0.096, 'False positive'),
            (1, 'True negative')
        ))
    )
    # If the test was positive, what's the likelihood of having cancer?
    test_distribution.filter(lambda e: 'positive' in e).plot()
    # False positive [=====================================   ] 92.01%
    #  True positive [===                                     ] 7.99%


    # Waiting at the bus stop
    # -----------------------
    # From https://www.gwern.net/docs/statistics/1994-falk#standard-problems-and-their-solution
    # It's 23:30, you are at the bus stop. Buses usually run each 30 minutes,
    # but you are not sure if they are operating at this time (60% chance).
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
    #        Not operating [==================                      ]  44.52%
    # Will arrive at 23:40 [====                                    ]  11.20%
    # Will arrive at 23:55 [====                                    ]  11.08%
    # Will arrive at 23:45 [====                                    ]  11.08%
    # Will arrive at 00:00 [====                                    ]  11.08%
    # Will arrive at 23:50 [====                                    ]  11.04%

    # It's now 23:55, and the bus has not yet arrived.
    bus_distribution.filter(lambda e: '23:' not in e).plot()
    #        Not operating [================================        ]  79.97%
    # Will arrive at 00:00 [========                                ]  20.03%


    # Monty Hall problem
    # ------------------
    # A car is put behind one of three doors.
    car_positions = Uniform(1, 2, 3)

    def best_strategy(car_position):
        # The participant chooses door number 1.

        # The host opens one of the other doors that does not contain the car.
        empty_door = {1: random.choice([2, 3]), 2: 3, 3: 2}[car_position]

        # Seeing the empty door, the participant may choose to switch.
        switched = {2: 3, 3: 2}[empty_door]

        # For *this* game, which strategy wins?
        return 'switch wins' if switched == car_position else 'stay wins'

        # Note all of this is equivalent to:
        # return 'stay' if car_position == 1 else 'switch'
        # But if you realised this, there would be no need for simulating.

    # Generate examples and compute the total likelihood of each strategy winning.
    car_positions.map(best_strategy).plot()
    # switch wins [===========================             ]  67.01%
    #   stay wins [=============                           ]  32.99%

    # Monty Hall - Ignorant Monty version
    # -----------------------------------
    # The host opens a remaining door at random.
    car_position_distribution = Uniform(1, 2, 3)
    opened_door_distribution = Uniform(1, 2, 3)
    game_distributions = car_position_distribution.join(opened_door_distribution)
    def process(examples):
        for car_position, opened_door in examples:
            # Participant choose door number 1. The opened door is neither the
            # participant's door, nor the door containing the car.
            if opened_door not in [car_position, 1]:
                # Seeing the empty door, the participant may choose to switch.
                switched = {2: 3, 3: 2}[opened_door]
                # For *this* game, which strategy wins?
                yield 'switch wins' if switched == car_position else 'stay wins'
    game_distributions.apply(process).plot()
    # switch wins [====================                    ]  50.01%
    #   stay wins [====================                    ]  49.99%