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

d = [(.2, 'Desk'), (.8, range(1, 8+1))]
print(list(possibilities(d)))

#print(select(d, id))
#print(select(d, lambda v: v not in [1, 2, 3, 4, 5, 6, 7])[8])

car_distribution = [1, 2, 3]
def open_door(car_position):
	if car_position == 1:
		return random.choice([2, 3])
	elif car_position == 2:
		return 3
	elif car_position == 3:
		return 2
def switch(opened_door):
	if opened_door == 2:
		return 3
	elif opened_door == 3:
		return 2
def best_strategy(car_position):
	opened_door = open_door(car_position)
	return 'switch' if switch(opened_door)==car_position else 'stay'
def process(examples):
	return [best_strategy(car_position) for car_position in examples]
print(select(car_distribution, process))
