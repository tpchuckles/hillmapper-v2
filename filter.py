
class WayFilter(object):
	min_slope = 0
	max_slope = 0
	min_length = 0
	max_length = 0
	
	def filter(self, ways):
		if self.min_length > 0:
			ways = filter(lambda w: w['length'] / 1609 > self.min_length, ways)
		if self.max_length > 0:
			ways = filter(lambda w: w['length'] / 1609 < self.max_length, ways)
		if self.min_slope > 0:
			ways = filter(lambda w: w['slope'] > self.min_slope, ways)
		if self.max_slope > 0:
			ways = filter(lambda w: w['slope'] < self.max_slope, ways)
		return ways
		
	