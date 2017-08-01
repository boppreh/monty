import random
from collections import Counter
def instantiate(d):
	if isinstance(d, list) and len(d) and isinstance(d[0], tuple) and len(d[0]) == 2:
		r = random.random()
		for key, value in d:
			r -= key
			if r <= 0:
				return instantiate(value)
	elif isinstance(d, (range, list, tuple, set)):
		return random.choice(d)
	else:
		return d
		

def select(d, fn):
	candidates = []
	while len(candidates) < 100000:
		candidate = instantiate(d)
		if fn(candidate):
			candidates.append(candidate)
	counter = Counter(candidates)
	total = sum(counter.values())
	return {value: count/total for value, count in counter.most_common()}

d = [(.2, 'Desk'), (.8, range(1, 8+1))]

print(select(d, id))
#print(select(d, lambda v: v not in [1, 2, 3, 4, 5, 6, 7])[8])