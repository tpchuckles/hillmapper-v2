import sys
import srtm
import math
import time
from imposm.parser import OSMParser
rad_earth_m = 6373000 # Radius of the earth in meters
level_4_min_slope=.15
level_3_min_slope=.12
level_2_min_slope=.09
level_1_min_slope=.05

class WayCollector(object):
	ways = []
	elevs = []
	coords = {}
	num_coords = 0
	num_ways = 0
	
	verbose = False
	min_lat_bound = None
	max_lat_bound = None
	min_lon_bound = None
	max_lon_bound = None
	longest_road = None
	
	roads = 'secondary', 'residential', 'tertiary', 'primary', 'primary_link', 'motorway', 'motorway_link', 'road', 'trunk', 'trunk_link', 'unclassified'
	ignored_surfaces = 'dirt', 'unpaved', 'gravel', 'sand', 'grass', 'ground'
	level_1_max_radius = 175
	level_1_weight = 1
	level_2_max_radius = 100
	level_2_weight = 1.3
	level_3_max_radius = 60
	level_3_weight = 1.6
	level_4_max_radius = 30
	level_4_weight = 2
	

	def load_srtm(self,filename):
		print "normally we'd be extracting from the SRTM file, but we won't, for now. you do not need to pass srtm files"
		
	def get_elevs(self, coords): #no longer used. elevations have been added to coords wayback thingymajig
		print "importing SRTM data"
		elevation_data = srtm.get_data()
		for osm_id in coords:
			self.coords[osm_id]=(self.coords[osm_id][0], self.coords[osm_id][1], elevation_data.get_elevation(self.coords[osm_id][0],self.coords[osm_id][0]))
			#print self.coords[osm_id]
	
	def load_osm(self, filename):
		# Reinitialize if we have a new file
		ways = []
		coords = {}
		num_coords = 0
		num_ways = 0
		
		# status output
		if self.verbose:
			sys.stderr.write("loading ways, each '-' is 100 ways, each row is 10,000 ways\n")
		
		posm = OSMParser(ways_callback=self.ways_callback)
		posm.parse(filename)
		#print {}
		# status output
		if self.verbose:
			sys.stderr.write("\n{} ways matched in {}, {} coordinates will be loaded, each '.' is 1% complete\n".format(len(self.ways), filename, len(self.coords)))
			total = len(self.coords)
			if total < 100:
				self.coords_marker = 1
			else:
				self.coords_marker = round(total/100)

		posm = OSMParser(coords_callback=self.coords_callback)
		posm.parse(filename)
		
		# status output
		if self.verbose:
			sys.stderr.write("\ncoordinates loaded. calculating curvature, each '.' is 1% complete\n")
			sys.stderr.flush()
	#	print self.coords
	#	for osm_id in range(len(self.coords)-1,-1,-1):
	#		if self.coords[id][0] < self.min_lat_bound:
	#			del self.coords[osm_id]
	#		elif self.coords[id][0] > self.max_lat_bound:
	#			del self.coords[osm_id]
	#		elif self.coords[osm_id][1] < self.min_lon_bound:
	#			del self.coords[osm_id]
	#		elif self.coords[osm_id][1] > self.max_lon_bound:
	#			del self.coords[osm_id]

	def coords_callback(self, coords):
		# callback method for coords
		elevation_data = srtm.get_data()
		elev=0
		for osm_id, lon, lat in coords:
			if self.min_lat_bound and lat < self.min_lat_bound:
				continue
			if self.max_lat_bound and lat > self.max_lat_bound:
				continue
			if self.min_lon_bound and lon < self.min_lon_bound:
				continue
			if self.max_lon_bound and lon > self.max_lon_bound:
				continue
			#elev=elevation_data.get_elevation(lat, lon)
			if osm_id in self.coords:
				elev=elevation_data.get_elevation(lat, lon)
				self.coords[osm_id] = (lat, lon, elev)
				#print self.coords[osm_id]
				# status output
				if self.verbose:
					self.num_coords = self.num_coords + 1
					if not (self.num_coords % self.coords_marker):
						sys.stderr.write('.')
						sys.stderr.flush()

	def ways_callback(self, ways):
		# callback method for ways
		for osmid, tags, refs in ways:
			
			# ignore circular ways (Maybe we don't need this)
			#if refs[0] == refs[-1]:
			#	continue
			
			if ('name' not in tags or tags['name'] == '') and ('ref' not in tags or tags['ref'] == ''):
				continue
			if 'surface' in tags and tags['surface'] in self.ignored_surfaces:
				continue
			if 'highway' in tags and tags['highway'] in self.roads:
				way = {'id': osmid, 'type': tags['highway'], 'refs': refs}
				if 'name' not in tags or tags['name'] == '':
					way['name'] = tags['ref']
				elif 'ref' in tags:
					way['name'] = unicode('{} ({})').format(tags['name'], tags['ref'])
				else:
					way['name'] = tags['name']
				if 'tiger:county' in tags:
					way['county'] = tags['tiger:county']
				else:
					way['county'] = ''
				if 'surface' in tags:
					way['surface'] = tags['surface']
				else:
					way['surface'] = 'unknown'
				self.ways.append(way)
				
				for ref in refs:
					self.coords[ref] = None
			
				# status output
				if self.verbose:
					self.num_ways = self.num_ways + 1
					if not (self.num_ways % 100):
						sys.stderr.write('-')
						if not self.num_ways % 10000:
							sys.stderr.write('\n')
						sys.stderr.flush()

	def calculate_slope(self):
		if self.verbose:
			i = 0
			total = len(self.ways)
			if total < 100:
				marker = 1
			else:
				marker = round(total/100)
		sections = []
		while len(self.ways):
			way = self.ways.pop(0)
			#print way
			# status output
			if self.verbose:
				i = i + 1
				if not (i % marker):
					sys.stderr.write('.')
					sys.stderr.flush()
			way['distance'] = 0.0
			way['slope'] = 0.0
			way['length'] = 0.0
			start = self.coords[way['refs'][0]]
			end = self.coords[way['refs'][-1]]
			#way['distance'] = self.distance_on_unit_sphere(start[0], start[1], end[0], end[1]) * rad_earth_m
			second = 0
			segments = []
			lengths=[]
			#way['distance'] = 0.0
			for ref in way['refs']:
				lengths=[]
				first = self.coords[ref]
				if not second:
					second = first
					continue
				try:
					distance=self.distance_on_unit_sphere(second[0], second[1], first[0], first[1]) * rad_earth_m
					deltaheight=second[2]-first[2]
					slope=math.fabs((deltaheight)/distance)
				except:
					#print "error on ref "+str(ref)
					#print second
					#print first
					#print distance
					slope=0
					distance=500.0
				if slope > level_4_min_slope:
					slope_level=4
				elif slope > level_3_min_slope:
					slope_level=3
				elif slope > level_2_min_slope:
					slope_level=2
				elif slope > level_1_min_slope:
					slope_level=1
				else:
					slope_level=0
				segments.append({'start': second, 'end': first, 'slope': slope, 'slope_level': slope_level, 'length': distance})
				lengths.append(distance)
			way['segments'] = segments
			way['length']=sum(lengths)
			way['distance']=sum(lengths)
			#print lengths
			#print way['distance']
			del way['refs'] # refs are no longer needed now that we have loaded our segments
			#print way
			#time.sleep(20)
			#for segment in segments:
			sections.append(way)
			#print sections[-1]['distance']
			#print sections[-1]
			#print len(way)
			#print len(sections)
			#if sections[-1]['name'] == 'Saddle Road (HI-200)':
			#	print sections[-1]
				#sys.exit()
		self.ways = sections
		#print self.ways
		#sys.exit()

	def sort_by_slope(self):
		if self.verbose:
			print "sorting"
		#self.ways = sorted(self.ways, key=lambda x: x)
		#print self.ways[1]['segments'][1]['slope']
		#self.ways = sorted(self.ways, key=lambda x: x['segments'][]['slope'])
		sortedways=[]
		maxes=[]
		#notinserted=true
		for i in range(0,len(self.ways)):
			seq = [x['slope'] for x in self.ways[i]['segments']]
			#print seq
			if len(seq):
				maxes.append(max(seq))
				self.ways[i]['slope']=max(seq)
			else:
				maxes.append(0)
		#print len(maxes)
		#print len(self.ways)
		#print sorted(maxes, reverse=True)
		self.ways=[x for (y,x) in sorted(zip(maxes,self.ways), reverse=True)]

	def cut_ways(self):
		#return
		i=0
		while i < len(self.ways):
			print len(self.ways)
			if len(self.ways[i]['segments']) > self.longest_road:
				#print "too long, splitting"
				#print self.ways[i]
				#print len(self.ways[i]['segments'])

				newway=self.ways[i].copy()
				lengthofnewway=self.longest_road-len(newway)
				self.ways[i]['segments']=self.ways[i]['segments'][:self.longest_road]
				#print self.ways[i]
				newway['segments']=newway['segments'][self.longest_road:]
				for segment in range(0, len(newway['segments'])):
					newway['segments'][segment]['start']=self.ways[i]['segments'][-1]['end']
				#print newway
				self.ways.append(newway)
				#print len(self.ways[i]['segments'])
				#print len(newway['segments'])
				
				#sys.exit()
			else:
				#print "perfect!"
				pass
			i+=1
			#pass



# From http://www.johndcook.com/python_longitude_latitude.html
	def distance_on_unit_sphere(self, lat1, long1, lat2, long2):
		if lat1 == lat2	 and long1 == long2:
			return 0

		# Convert latitude and longitude to 
		# spherical coordinates in radians.
		degrees_to_radians = math.pi/180.0
			
		# phi = 90 - latitude
		phi1 = (90.0 - lat1)*degrees_to_radians
		phi2 = (90.0 - lat2)*degrees_to_radians
			
		# theta = longitude
		theta1 = long1*degrees_to_radians
		theta2 = long2*degrees_to_radians
		
		# Compute spherical distance from spherical coordinates.
			
		# For two locations in spherical coordinates 
		# (1, theta, phi) and (1, theta, phi)
		# cosine( arc length ) = 
		#	 sin phi sin phi' cos(theta-theta') + cos phi cos phi'
		# distance = rho * arc length
	
		cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + math.cos(phi1)*math.cos(phi2))
		arc = math.acos( cos )

		# Rem	ember to multiply arc by the radius of the earth 
		# in your favorite set of units to get length.
		return arc