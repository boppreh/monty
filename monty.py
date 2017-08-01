import random
from collections import Counter

def possibilities(d, scale=1):
	if isinstance(d, dict):
		for key, value in d.items():
			yield from possibilities(value, scale*key)
	elif isinstance(d, list) and len(d) and isinstance(d[0], tuple) and len(d[0]) == 2:
		for key, value in d:
			yield from possibilities(value, scale*key)
	elif isinstance(d, (range, list, tuple, set)):
		length = len(d)
		for value in d:
			yield from possibilities(value, scale/length)
	else:
		yield (scale, d)

def examples(p):
	p = list(p)
	while True:
		r = random.random()
		for probability, value in p:
			r -= probability
			if r <= 0:
				yield value
				break
		
def select(d, process=lambda c: c, n=100000):
	counter = Counter(process(e for i, e in zip(range(n), examples(possibilities(d)))))
	total = sum(counter.values())
	return {value: count/total for value, count in counter.most_common()}

def plot(dictionary):
	items = [(str(key), value) for key, value in dictionary.items()]
	longest_key = max(len(key) for key, value in items)
	for key, value in sorted(items, key=lambda a: a[1], reverse=True):
		bar = '['+(round(value * 40) * '=').ljust(40)+']'
		print(key.rjust(longest_key), bar, '{:.2%}%'.format(value))

if __name__ == '__main__':
	#d = [(.2, 'Desk'), (.8, range(1, 8+1))]
	#print(list(possibilities(d)))

	#print(select(d, id))
	#print(select(d, lambda v: v not in [1, 2, 3, 4, 5, 6, 7])[8])

	# A car is put behind one of three doors, evenly distributed.
	car_distribution = [1, 2, 3]

	# The participant chooses number 1.

	# The host opens one of the other doors, revealing it's empty.
	def show_empty_door(car_position):
		if car_position == 1:
			return random.choice([2, 3])
		elif car_position == 2:
			return 3
		elif car_position == 3:
			return 2

	# Seeing the empty door, the participant may choose to switch.
	def switch(empty_door):
		if empty_door == 2:
			return 3
		elif empty_door == 3:
			return 2

	# For a given game, what is the strategy that wins the car?
	def best_strategy(car_position):
		empty_door = show_empty_door(car_position)
		if switch(empty_door) == car_position:
			return 'switch'
		else:
			return 'stay'

	# Generate a ton of examples and compute the likelihood of each strategy
	# winning.
	def process(examples):
		return [best_strategy(car_position) for car_position in examples]
	evaluation = select(car_distribution, process)
	# evaluation = {'switch': 0.6639, 'stay': 0.3361}

	plot(evaluation)
	# switch [==========================              ] 66.39%%
	#   stay [=============                           ] 33.61%%