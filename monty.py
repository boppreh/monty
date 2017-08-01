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

def flatten_distribution(d, scale=1):
    """
    Transform a nested distribution into a flat list of pairs
    (probability, value). If the "distribution" is just a list of values,
    assume uniform probability.
    """
    if isinstance(d, dict):
        for key, value in d.items():
            yield from flatten_distribution(value, scale*key)
    elif isinstance(d, list) and len(d) and isinstance(d[0], tuple) and len(d[0]) == 2:
        for key, value in d:
            yield from flatten_distribution(value, scale*key)
    elif isinstance(d, (range, list, tuple, set)):
        length = len(d)
        for value in d:
            yield from flatten_distribution(value, scale/length)
    else:
        yield (scale, d)

def generate_examples(distribution):
    """
    Given a (potentially nested) distribution, generates infniite random
    instances drawn from this distribution.
    """
    total = 0
    running = []
    for probability, value in flatten_distribution(distribution):
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

def select(distribution, process=lambda c: c, n=100000):
    """
    Given a distribution and a function to process lists of examples, returns
    the distribution of processed examples.
    """
    examples = generate_examples(distribution)
    counter = Counter(process(next(examples) for i in range(n)))
    total = sum(counter.values()) # Note that `process` may change the number of examples.
    return {value: count/total for value, count in counter.most_common()}

def plot(dictionary):
    """
    Prints a horizontal bar plot of values in the given dictionary.
    """
    items = [(str(key), value) for key, value in dictionary.items()]
    longest_key = max(len(key) for key, value in items)
    for key, value in sorted(items, key=lambda a: (a[1], a[0]), reverse=True):
        bar = '['+(round(value * 40) * '=').ljust(40)+']'
        print(key.rjust(longest_key), bar, '{:>7.2%}'.format(value))

if __name__ == '__main__':
    # Letter search
    # -------------
    # From https://www.gwern.net/docs/statistics/1994-falk#standard-problems-and-their-solution :
    # The letter may be in the desk or one of the 8 drawers.
    distribution = [(0.2, 'Desk'), (0.8, [1,2,3,4,5,6,7,8])]

    # If I opened the first drawer and it's not there...
    plot(select(distribution, lambda e: [c for c in e if c != 1]))
    # Desk [=========                               ] 22.26%
    #    4 [=====                                   ] 11.26%
    #    3 [====                                    ] 11.15%
    #    6 [====                                    ] 11.14%
    #    7 [====                                    ] 11.08%
    #    8 [====                                    ] 11.05%
    #    2 [====                                    ] 11.04%
    #    5 [====                                    ] 11.04%

    # If I opened the first 7 drawers and it's there...
    plot(select(distribution, lambda e: [c for c in e if c not in [1,2,3,4,5,6,7]]))
    # Desk [===========================             ] 66.93%
    #    8 [=============                           ] 33.07%


    # Breast cancer
    # -------------
    # Taken from https://betterexplained.com/articles/an-intuitive-and-short-explanation-of-bayes-theorem/ :
    # 1% of women have breast cancer.
    cancer_distribution = [(0.01, 'cancer'), (0.99, 'no cancer')]
    def positive_mammogram(status):
        # 80% of mammograms detect breast cancer when it is there.
        # 9.6% of mammograms detect breast cancer when it’s not there.
        return flip(0.8 if status == 'cancer' else 0.096)
    # If the test was positive, what's the new likelihood of having cancer?
    plot(select(cancer_distribution, lambda e: [c for c in e if positive_mammogram(c)]))
    # no cancer [=====================================   ]  91.95%
    #    cancer [===                                     ]   8.05%

    # Alternative solution: model the test results in the distribution itself.
    # Note that probabilities are taken in order, so 1 is taken just as "all rest".
    distribution = [
        # Cancer
        (0.01, [
            (0.8, 'True positive'),
            (1, 'False negative')
        ]),
        # No cancer
        (1, [
            (0.096, 'False positive'),
            (1, 'True negative')
        ])
    ]
    # If the test was positive, what's the likelihood of having cancer?
    plot(select(distribution, lambda e: [c for c in e if 'positive' in c]))
    # False positive [=====================================   ] 92.01%
    #  True positive [===                                     ] 7.99%


    # Monty Hall problem
    # ------------------
    # A car is put behind one of three doors.
    car_positions = [1, 2, 3]

    def best_strategy(car_position):
        # The participant chooses door number 1.

        # The host opens one of the other doors that does not contain the car.
        empty_door = {1: random.choice([2, 3]), 2: 3, 3: 2}[car_position]

        # Seeing the empty door, the participant may choose to switch.
        switched = {2: 3, 3: 2}[empty_door]

        # For this game, which strategy wins?
        return 'switch' if switched == car_position else 'stay'

        # Note all of this is equivalent to:
        # return 'stay' if car_position == 1 else 'switch'
        # But if you realised this, there would be no need for simulating.

    # Generate examples and compute the total likelihood of each strategy winning.
    plot(select(
        car_positions,
        lambda e: (best_strategy(car_position) for car_position in e)
    ))
    # switch [===========================             ]  66.63%
    #   stay [=============                           ]  33.37%