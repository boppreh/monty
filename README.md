monty
=====

`monty` is a pure-Python library for computing and analyzing discrete distributions. It is useful for exploring hypothetical scenarios and solving tricky statistical problems. The name `monty` comes from the [*Monty Hall problem*](https://en.wikipedia.org/wiki/Monty_Hall_problem), a probability puzzle.

The workhorse of this library is the `Distribution` class, which internally stores the discrete distribution as a list of pairs `(value, odds)`. The `Distribution` class has functions for changing the values, updating the odds, generating random values, and plotting. A number of shortcuts and helpers is also included.

**Note on terminology**: this library uses the term *odds* to mean any non-negative value that somehow associates a value with a likelihood. Odds are not normalized like probabilities, so you can have `Distribution(Tails=25, Heads=50)`, where the numbers `25` and `50` are used only for relative comparison (*heads* appears twice as more than *tails*, that is, 66% vs 33%). Those numbers are converted to probabilities when plotting, but under the hood they are kept as-is. I'm not sure if *odds* is the correct term, but it's an important distinction.

## Table of contents

- [Constructing](#constructing)
- [Built-in distributions](#built-in-distributions)
- [Joining](#joining)
- [Visualizing](#visualizing)
- [Updating](#updating)
    - [Map](#map)
    - [Filter](#filter)
- [Simulating](#simulating)
- [Expected value / utility function](#expected_value-utility_function)
- [Exmples](#examples)

<a name="constructing"/>

## Constructing

There are several ways to construct a distribution. The following three examples are all equivalent:

- Explicit pairs: `Distribution(('Heads', 0.5), ('Tails', 0.5))`.
- Dictionary: `Distribution({'Heads': 0.5, 'Tails': 0.5})`.
- Keyword arguments: `Distribution(Heads=0.5, Tails=0.5)`.

Since the library operates on *odds*, not *probabilities*, the total doesn't have to sum up to 1: `Distribution(Heads=9, Tails=1)`: 9/10 chance of *heads*.

If you do choose to enter probabilities (odds summing to 1), you can use the special value `REST` to avoid computing the probability of the last value: `Distribution(Heads=0.499, Tails=0.499, Sideways=REST)`.

Additionally, the classes `Uniform`, `Fixed`, `Range`, `Count`, `Permutations` are constructred differently, but behave exactly like `Distribution` after initialization:

- `Uniform('Heads', 'Tails')`: automatically distributes the odds equally between all items.
- `Fixed('Heads')`: only allows one value, with 100% probability.
- `Range(10)`: uniform distribution of values `[0, 1, ... 8, 9]`.
- `Count(10)`: uniform distribution of values `[1, 2, ... 8, 10]`.
- `Permutations('Red', 'Blue', 'Green')`: uniform distribution of all possible orderings (`red blue green` or `blue red green` or `blue green red`, etc).

Finally, the values may also be distributions, in a nested manner:

```python
# 99% of the chance of the coin being legitimate, with an unknown value
# uniformly distributed.
coin_value = Distribution({
    Uniform(1, 5, 10, 25, 50, 100): 0.99,
    'Counterfeit': REST,
})
```

<a name="built-in-distributions"/>

## Built-in distributions

The `monty` library comes with a number of distributions commonly used in examples:

```python
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
# https://en.wikipedia.org/wiki/Lottery_mathematics
# Typical 6/49 game.
lottery = Distribution(Win=1/13983816, Loss=REST)
powerball = Distribution(Win=1/292201338, Loss=REST)
# http://www.lightningsafety.noaa.gov/odds.shtml
# Chance of being struck by lightning in your lifetime.
lightning_strike = Distribution({'Struck by lightning': 1/13500, 'Safe': REST})
# http://news.nationalgeographic.com/2016/02/160209-meteorite-death-india-probability-odds/
# Chance of being killed by meteorite in your lifetime.
meteorite = Distribution({'Killed by meteorite': 700000, 'Safe': REST})
```

<a name="joining"/>

## Joining

You can compute the combinations of two or more distributions with the function `join`, creating tuples of combinations with multiplied probability:

```python
join(coin, dice).plot()
#                 ('Heads', 1)   8.33% [===                                     ]
#                 ('Heads', 2)   8.33% [===                                     ]
#                 ('Heads', 3)   8.33% [===                                     ]
#                 ('Heads', 4)   8.33% [===                                     ]
#                 ('Heads', 5)   8.33% [===                                     ]
#                 ('Heads', 6)   8.33% [===                                     ]
#                 ('Tails', 1)   8.33% [===                                     ]
#                 ('Tails', 2)   8.33% [===                                     ]
#                 ('Tails', 3)   8.33% [===                                     ]
#                 ('Tails', 4)   8.33% [===                                     ]
#                 ('Tails', 5)   8.33% [===                                     ]
#                 ('Tails', 6)   8.33% [===                                     ]
```

Additionally, the multiplication operator `*` has been overloaded to join a distribution with itself *n* times.

```python
(coin*2).plot()
#           ('Heads', 'Heads')  25.00% [==========                              ]
#           ('Heads', 'Tails')  25.00% [==========                              ]
#           ('Tails', 'Heads')  25.00% [==========                              ]
#           ('Tails', 'Tails')  25.00% [==========                              ]
```

**Warning**: joining two distributions, `join(A, B)`, results in a distribution where the values are pairs `(a, b)`. Joining this resulting distribution with another one, `join(join(A, B), C)`, will not result in a distribution of triples `(a, b, c)`, but of nested pairs `((a, b), c)`. In the same vein, `A*1` results in values wrapped in a single-value tuple `(a,)`. This is why the addition operator was not overloaded, otherwise `A+B+C` would result in a confusingly nested distribution. Use `join(A, B, C)` in this case.

<a name="visualizing"/>

## Visualizing

You can retrieve the contents of a distribution in three ways:

- As a list of pairs `(value, odds)` as in `print(distribution)`, `for value, odds in distribution: ...`, `dict(distribution)`, `len(distribution)` (but **not** `distribution[0]`, see next).
- Fetching the odds for a specific value: `distribution[value]` (e.g. `coin['Tails'] == 0.5`).
- Plotting to the terminal: `distribution.plot(sort=True, filter=True)`.

```python
card_suits.plot()
#                    Clubs  25.00% [==========                              ]
#                 Diamonds  25.00% [==========                              ]
#                   Hearts  25.00% [==========                              ]
#                   Spades  25.00% [==========                              ]
```

<a name="updating"/>

## Updating

Distributions are immutable objects, but they support creating modified copies. Remember the distribution is modeled as a list of pairs `(value, odds)`. There are two main functions to update a distribution: `distribution.map` updates each `value`; and `distribution.filter` updates each `odds`.

<a name="map"/>

### Map

`distribution.map` takes a function `fn` as parameter, and returns a new distribution `(fn(value), odds)`. If multiple values mapped to the same new value, their odds will add up:

```python
dice.map(lambda v: v > 4).plot()
#                    False  66.67% [===========================             ]
#                     True  33.33% [=============                           ]
```

Because of this behavior, `map` is aliased to `group` and `group_by`.

Often your `value` will be a tuple. For example, in `dice * 4` the values are tuples of four dice rolls. To help mapping in these situations, the library includes a number of comparison operators (`lt`, `le`, `eq`, `ne`, `gt`, `ge`), and basic arithmetic operators (`add`, `sub`, `difference` (absolute), `product`). For example, the sum of four dice rolls: `(dice*4).map(add)`.

Also, `distribution.starmap` invokes `fn(*value)` instead of `fn(value)`, making it easier to access each individual item. For example, `join(coin, dice).starmap(lambda toss, roll: toss == 'Heads' and roll > 4)`.

**Note**: your mapping function may return another Distribution object, which is then integrated into the parent distribution. This allows you to split a value, or remove it completely. This is a feature of the construction, not of the mapping.

<a name="filter"/>

### Filter

This functions returns a copy of the distribution, with modified odds for each value. Each pair `(value, odds)` is replaced with `(value, odds*fn(value))`. Note that the odds are updating *in relation to the previous odds*, like a refinement, and not a replacement.

`distribution.filter` can be used in several ways, depending on the type of the argument:

- List: allows only values present in the list, changing the odds of any other value to 0. Think of it as focusing the distribution.

```python
dice.filter([1, 2, 5, 6]).plot(sort=False)
#                        1  25.00% [==========                              ]
#                        2  25.00% [==========                              ]
#                        3   0.00% [                                        ]
#                        4   0.00% [                                        ]
#                        5  25.00% [==========                              ]
#                        6  25.00% [==========                              ]
```

- Dictionary, Distribution or keyword arguments: multiplies the odds by the corresponding value.

```python
dice.filter({1: 1, 2: 1, 3: 0.5, 4: 0.5, 5: 1, 6: 1}).plot(sort=False)
#                        1  16.67% [=======                                 ]
#                        2  16.67% [=======                                 ]
#                        3   8.33% [===                                     ]
#                        4   8.33% [===                                     ]
#                        5  16.67% [=======                                 ]
#                        6  16.67% [=======                                 ]
```

- Function: calls `fn(value)` and expects a multiplier back (note that `True == 1` and `False == 0`, so boolean results are ok).

```python
# Functions returns boolean:
dice.filter(lambda v: v % 2 == 1).plot(sort=False)
#                        1  33.33% [=============                           ]
#                        2   0.00% [                                        ]
#                        3  33.33% [=============                           ]
#                        4   0.00% [                                        ]
#                        5  33.33% [=============                           ]
#                        6   0.00% [                                        ]
```

```python
# Function returns multiplier
dice.filter(lambda v: 1 if v % 2 else 0.5).plot(sort=False)
#                        1  22.22% [=========                               ]
#                        2  11.11% [====                                    ]
#                        3  22.22% [=========                               ]
#                        4  11.11% [====                                    ]
#                        5  22.22% [=========                               ]
#                        6  11.11% [====                                    ]
```

- No argument: equivalent to `filter(lambda v: bool(v))`, filters away "falsy" values (i.e. removes `False`, `0`, `None`, `[]`, `{}`, `""`).

**Note**: the comparison operators mentioned in the Map section (`lt`, `le`, `eq`, `ne` (aliased to `not_equal(s)`), `gt`, `ge`) are also useful here. But the result from mapping versus filtering based on them is completely different. *Mapping* a condition means asking "divide the values into the ones that obey or not this condition". *Filtering* on a condition, on the other hand, means asking "ignore the values that don't obey this condition". Both are useful in their own ways. For example:

```python
(2*coin).map(not_equals).plot()
#                    False  50.00% [====================                    ]
#                     True  50.00% [====================                    ]
```

```python
(2*coin).filter(not_equals).plot()
#       ('Heads', 'Tails')  50.00% [====================                    ]
#       ('Tails', 'Heads')  50.00% [====================                    ]
#       ('Heads', 'Heads')   0.00% [                                        ]
#       ('Tails', 'Tails')   0.00% [                                        ]
```

<a name="simulating"/>

## Simulating

The function `distribution.generate(n)` returns *n* random values sampled from the distribution (or infinite values, if `n==-1` or not specified).

```python
for card in deck.generate(10):
    print('Is this your card?', card)

# Is this your card? (9, 'Clubs')
# Is this your card? (2, 'Diamonds')
# Is this your card? (5, 'Hearts')
# Is this your card? ('Jack', 'Spades')
# Is this your card? (4, 'Hearts')
# Is this your card? (8, 'Clubs')
# Is this your card? ('King', 'Hearts')
# Is this your card? (9, 'Diamonds')
# Is this your card? (5, 'Diamonds')
# Is this your card? (2, 'Clubs')
```

Additionally, sometimes operations are too complex to fit in a pattern of `map` and `filter`, such as conditions that depend on consecutive draws. In these cases, the method `distribution.monte_carlo(fn, n=100000)` generates *n* examples from the distribution, feeds them as a generator to `fn`, and creates a new distribution from the list of values returned by `fn`. Note that operations performed this way are probabilistic, therefore the result may not be precise.

```python
def remove_rising(nums):
    last = None
    for num in nums:
        if last is not None and num != last+1:
            yield num
        last = num

dice.monte_carlo(remove_rising).plot()
#                            1  19.46% [========                                ]
#                            5  16.23% [======                                  ]
#                            4  16.18% [======                                  ]
#                            3  16.10% [======                                  ]
#                            2  16.03% [======                                  ]
#                            6  16.00% [======                                  ]
```

<a name="expected_value-utility_function"/>

## Expected value / utility function

Sometimes you want to summarize a complex distribution into a single value. For this purpose, the Distribution class implements the `distribution.expected_value` property and the `distribution.utlity(fn)` method.

```
# How much should you pay for a ticket to a $400,000,000 jackpot at a 1/13983816 chance?
lottery.map(Win=400_000_000, Loss=0).expected_value
# 28.604495368074065

# A dollar is less useful for a millionaire than for a poorer person.
# Use a utility function with a logarithmic scale.
import math
lottery.map(Win=400_000_000, Loss=0).utility(lambda v: math.log(v, 1.1) if v else 0)
# 1.4861175606104777e-05
```

<a name="examples"/>

## Examples

    from monty import *

### Breast cancer

```python
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
```


### Waiting at the bus stop

```python
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
```

### Monty Hall problem

```python
# A car is put behind one of three doors.
car_positions = Uniform(1, 2, 3)

# The participant starts selecting door number 1.

def open_door(car_position):
    # The host opens one of the other doors that does not contain the car.
    opened_door = {1: random.choice([2, 3]), 2: 3, 3: 2}[car_position]
    return (car_position, opened_door)

def best_strategy(car_position, opened_door):
    # Seeing the empty door, the participant may choose to switch.
    switched = {2: 3, 3: 2}[opened_door]

    # For *this* game, which strategy wins?
    return 'Switching wins' if switched == car_position else 'Staying wins'

    # Note that because only two doors remain, and the strategies are
    # always opposites, you can negate the final condition and simplify
    # to just "return 'stay' if car_position == 1 else 'switch'".
    # But if you realise this, the result becomes trivial.

# Compute the total likelihood of each strategy winning.
car_positions.map(open_door).starmap(best_strategy).plot()
#           Switching wins [===========================             ]  66.67%
#             Staying wins [=============                           ]  33.33%
```

### Monty Hall - Ignorant Monty version

```python
# (using `best_strategy` from previuos example)
#
# Same setup as classic Monty Hall, now with host opening door 2 or 3 at
# random.
opened_doors = Uniform(2, 3)

# But we only look at situations where the opened door *just happened* to
# not be the car door.
game = join(car_positions, opened_doors).filter(not_equals)

# What are the strategy likelihoods for winning then?
game.starmap(best_strategy).plot()
#            Switching wins [====================                    ]  50.00%
#              Staying wins [====================                    ]  50.00%
```

### Throw two dice

```python
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
```

### Unbiased flip from biased coin

```python
# From John von Neuman (1951)

# I want a fair coin flip, but I don't trust this coin. Can I "unbias" it?
b_coin = Distribution(Heads=0.6, Tails=REST)

# Yes! Flip it twice, and retry until they are different. Then look at
# the first one.
(2*b_coin).filter(not_equals).map(first).plot()
#                    Tails  50.00% [====================                    ]
#                    Heads  50.00% [====================                    ]
```

### Mixing solutions

```python
# Fun fact: you can also use likelihood distributions to keep track of
# concentrations in solutions. `Solution` is a subclass of `Distribution`
# that overloads `+`, `*`, and `/` to behave like a physical mix. This is
# possible because odds are not normalized like probabilities, so we use
# them to keep track of total volume.
#
# Think of the probabilities as "what is the chance of a random molecule
# of this mix being of type X?".

# 200 units of water and 600 units of pure orange.
juice = Solution(water=200, orange=600).plot()
#                   orange  75.00% [==============================          ]
#                    water  25.00% [==========                              ]

# 100 units of sugar water at 5%
sugar_water = Solution(water=95, sugar=5).plot()
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

# Mix 1 unit of juice and sugar water at 50/50, resulting in 2.5% sugar.
Solution({juice: 1, sugar_water: 1}).plot()
#                    water  60.00% [========================                ]
#                   orange  37.50% [===============                         ]
#                    sugar   2.50% [=                                       ]
```

### Detecting coin bias

```python
# We got a coin from a factory of biased coins. The factory makes 11 different
# coins, each type flipping heads anywhere from 0% to 100% of the time.
all_coin_types = [Distribution(Heads=i/10, Tails=REST) for i in range(11)]

# We get one of these coins, but don't know which type.
# (`force_flatten=False` is required so `Uniform` doesn't merge all Heads/Tails
# probabilities. We could also just not use `Distribution` for the coin types.)
coins = Uniform(*all_coin_types, force_flatten=False)

coins.plot()
# (('Heads', 0.0), ('Tails', 1.0))   9.09% [====                                    ]
# (('Heads', 0.1), ('Tails', 0.9))   9.09% [====                                    ]
# (('Heads', 0.2), ('Tails', 0.8))   9.09% [====                                    ]
# (('Heads', 0.3), ('Tails', 0.7))   9.09% [====                                    ]
# (('Heads', 0.4), ('Tails', 0.6))   9.09% [====                                    ]
# (('Heads', 0.5), ('Tails', 0.5))   9.09% [====                                    ]
# (('Heads', 0.6), ('Tails', 0.4))   9.09% [====                                    ]
# (('Heads', 0.7), ('Tails', 0.3))   9.09% [====                                    ]
# (('Heads', 0.8), ('Tails', 0.1))   9.09% [====                                    ]
# (('Heads', 0.9), ('Tails', 0.0))   9.09% [====                                    ]
# (('Heads', 1.0), ('Tails', 0.0))   9.09% [====                                    ]

# We don't know yet, but our coin is the 70%-Heads coin. Toss it 10 times.
tosses = ['Heads'] * 7 + ['Tails'] * 3
random.shuffle(tosses)

# Update the chance of each coin type according to their predicted probability
# for that coin toss.
for toss in tosses:
    # Must be normalized to avoid losing precision.
    coins = coins.filter(lambda c: c[toss]).normalized()

coins.plot(sort=False)
# (('Heads', 0.0), ('Tails', 1.0))   0.00% [                                        ]
# (('Heads', 0.1), ('Tails', 0.9))   0.00% [                                        ]
# (('Heads', 0.2), ('Tails', 0.8))   0.09% [                                        ]
# (('Heads', 0.3), ('Tails', 0.7))   0.99% [                                        ]
# (('Heads', 0.4), ('Tails', 0.6))   4.67% [==                                      ]
# (('Heads', 0.5), ('Tails', 0.5))  12.88% [=====                                   ]
# (('Heads', 0.6), ('Tails', 0.4))  23.63% [=========                               ]
# (('Heads', 0.7), ('Tails', 0.3))  29.32% [============                            ]
# (('Heads', 0.8), ('Tails', 0.2))  22.12% [=========                               ]
# (('Heads', 0.9), ('Tails', 0.1))   6.31% [===                                     ]
# (('Heads', 1.0), ('Tails', 0.0))   0.00% [                                        ]
```


### Makeshift dice

```python
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

(5 * d4).map(sum).plot(sort=False)
#                        5   0.10% [                                        ]
#                        6   0.49% [                                        ]
#                        7   1.46% [=                                       ]
#                        8   3.42% [=                                       ]
#                        9   6.35% [===                                     ]
#                       10   9.86% [====                                    ]
#                       11  13.18% [=====                                   ]
#                       12  15.14% [======                                  ]
#                       13  15.14% [======                                  ]
#                       14  13.18% [=====                                   ]
#                       15   9.86% [====                                    ]
#                       16   6.35% [===                                     ]
#                       17   3.42% [=                                       ]
#                       18   1.46% [=                                       ]
#                       19   0.49% [                                        ]
#                       20   0.10% [                                        ]
# Nope.
```

### Dungeons and confused dragons

```python
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
```

### Nontransitive dice

```python
# Three 6-sided dices with modified numbers.
dice_a = Uniform(2, 2, 4, 4, 9, 9)
dice_b = Uniform(1, 1, 6, 6, 8, 8)
dice_c = Uniform(3, 3, 5, 5, 7, 7)

# Expected value is the same (within float tolerance).
import math
assert math.isclose(dice_a.expected_value, dice_b.expected_value)
assert math.isclose(dice_b.expected_value, dice_c.expected_value)

# But they behave like rock paper scissors:

join(dice_a, dice_b).map(lt).map(['A wins', 'B wins']).plot()
#                   A wins  55.56% [======================                  ]
#                   B wins  44.44% [==================                      ]

join(dice_b, dice_c).map(lt).map(['B wins', 'C wins']).plot()
#                   B wins  55.56% [======================                  ]
#                   C wins  44.44% [==================                      ]

join(dice_c, dice_a).map(lt).map(['C wins', 'A wins']).plot()
#                   C wins  55.56% [======================                  ]
#                   A wins  44.44% [==================                      ]
```

### Sleeping beauty

```python
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

def verify_guess(actual, day, guess):
    if actual == guess:
        return 'Correct ' + guess
    else:
        return 'Incorrect'
guesses.starmap(verify_guess).plot()

#                Incorrect  50.00% [====================                    ]
#            Correct Tails  33.33% [=============                           ]
#            Correct Heads  16.67% [=======                                 ]

# She is right more often by guessing tails. But no event gave her any
# evidence. Should she believe the coin landed tails?
```

### Ellsberg Paradox

```python
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
```