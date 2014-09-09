import os
import copy
import ast
import sys
import argparse
from collector import WayCollector
from filter import WayFilter
from output import TabOutput
from output import SingleColorKmlOutput
from output import MultiColorKmlOutput

parser = argparse.ArgumentParser(description='Find the roads that are most steep in an Open Street Map (OSM) XML file.')
parser.add_argument('-v', action='store_true', help='Verbose mode, showing status output')
parser.add_argument('-t', action='store_true', help='Display tabular output')
parser.add_argument('--no_kml', action='store_true', help='Do not generate a KML file. By default a KML file is generated with the name of the input file followed by .kml')
parser.add_argument('--km', action='store_true', help='Output kilometers instead of miles.')
parser.add_argument('--output_path', type=str, default='.', help='The path under which output files should be written')
parser.add_argument('--output_basename', type=str, default=None, help='The base of the name for output files. This will be appended with a suffix and extension')
parser.add_argument('--colorize', action='store_true', help='Colorize KML lines based on the slope of the road at each segment. Without this option roads will be lines of a single color. For large regions this may make Google Earth run slowly.')
parser.add_argument('--min_length', type=float, default=0, help='the minimum length of a way that should be included, in miles, 0 for no minimum. The default is 2.0')
parser.add_argument('--max_length', type=float, default=0, help='the maximum length of a way that should be included, in miles, 0 for no maximum. The default is 0')
parser.add_argument('--min_slope', type=float, default=0.05, help='the minimum slope of a way that should be included, 0 for no minimum. The default is 0 which catches most twisty roads.')
parser.add_argument('--max_slope', type=float, default=0, help='the maximum curvature of a way that should be included, 0 for no maximum. The default is 0')
parser.add_argument('--longest_road', type=int, default=10, help='the longest road in number of sections before splitting into pieces')
parser.add_argument('--add_kml', metavar='PARAMETERS', type=str, action='append', help='Output an additional KML file with alternate output parameters. PARAMETERS should be a comma-separated list of option=value that may include any of the following options: colorize, min_curvature, max_curvature, min_length, and max_length. Example: --add_kml colorize=1,min_curvature=1000')
parser.add_argument('--level_1_max_radius', type=int, default=175, help='the maximum radius of a curve (in meters) that will be considered part of level 1. Curves with radii larger than this will be considered straight. The default is 175')
parser.add_argument('--level_1_weight', type=float, default=1, help='the weight to give segments that are classified as level 1. Default 1')
parser.add_argument('--level_2_max_radius', type=int, default=100, help='the maximum radius of a curve (in meters) that will be considered part of level 2. The default is 100')
parser.add_argument('--level_2_weight', type=float, default=1.3, help='the weight to give segments that are classified as level 2. Default 1.3')
parser.add_argument('--level_3_max_radius', type=int, default=60, help='the maximum radius of a curve (in meters) that will be considered part of level 3. The default is 60')
parser.add_argument('--level_3_weight', type=float, default=1.6, help='the weight to give segments that are classified as level 3. Default 1.6')
parser.add_argument('--level_4_max_radius', type=int, default=30, help='the maximum radius of a curve (in meters) that will be considered part of level 4. The default is 30')
parser.add_argument('--level_4_weight', type=float, default=2, help='the weight to give segments that are classified as level 4. Default 2')
parser.add_argument('--ignored_surfaces', type=str, default='dirt,unpaved,gravel,sand,grass,ground', help='a list of the surfaces that should be ignored. The default is dirt,unpaved,gravel,sand,grass,ground')
parser.add_argument('--highway_types', type=str, default='secondary,residential,tertiary,primary,primary_link,motorway,motorway_link,road,trunk,trunk_link,unclassified', help='a list of the highway types that should be included. The default is secondary,residential,tertiary,primary,primary_link,motorway,motorway_link,road,trunk,trunk_link,unclassified')
parser.add_argument('--min_lat_bound', type=float, default=None, help='The minimum latitude to include.')
parser.add_argument('--max_lat_bound', type=float, default=None, help='The maximum latitude to include.')
parser.add_argument('--min_lon_bound', type=float, default=None, help='The minimum longitude to include.')
parser.add_argument('--max_lon_bound', type=float, default=None, help='The maximum longitude to include.')
parser.add_argument('--straight_segment_split_threshold', type=float, default=1.5, help='If a way has a series of non-curved segments longer than this (miles), the way will be split on that straight section. Use 0 to never split ways. The default is 1.5')
parser.add_argument('file', type=argparse.FileType('r'), nargs='+', help='the input file. Should be an OSM XML file or an SRTM1 hgt file (need at least one of each).')
args = parser.parse_args()

collector = WayCollector()
default_filter = WayFilter()
collector.verbose = args.v
collector.min_lat_bound = args.min_lat_bound
collector.max_lat_bound = args.max_lat_bound
collector.min_lon_bound = args.min_lon_bound
collector.max_lon_bound = args.max_lon_bound
collector.longest_road = args.longest_road
default_filter.min_length = args.min_length
default_filter.max_length = args.max_length
default_filter.min_slope = args.min_slope
default_filter.max_slope = args.max_slope


for file in args.file:
	if args.v:
		sys.stderr.write("Loading {}\n".format(file.name))
		print os.path.splitext(file.name)[-1]
	if os.path.splitext(file.name)[-1] == '.osm':
		collector.load_osm(file.name)
	if os.path.splitext(file.name)[-1] == '.hgt':
		collector.load_srtm(file.name)
#print collector.ways[1]
#collector.filter(collector.coords)

#print "length ways="+str(len(collector.ways))
#print "length coords="+str(len(collector.coords))
#print collector.coords
#collector.get_elevs(collector.coords)
#print collector.coords
collector.calculate_slope()
#print collector.ways[1]
collector.cut_ways()
collector.sort_by_slope()
#print collector.ways[1]
#sys.exit()
#print "length ways="+str(len(collector.ways))
#print "length coords="+str(len(collector.coords))

if args.t:
	tab = TabOutput(default_filter)
	tab.output(collector.ways)

# Generate KML output
if not args.no_kml:
	if args.v:
		sys.stderr.write("generating KML output\n")
	
	if args.output_path is None:
		path = os.path.dirname(file.name)
	else:
		path = args.output_path
	if args.output_basename is None:
		basename = os.path.basename(file.name)
		parts = os.path.splitext(basename)
		basename = parts[0]
	else:
		basename = os.path.basename(args.output_basename)
		
	if args.colorize:
		kml = MultiColorKmlOutput(default_filter)
	else:
		kml = SingleColorKmlOutput(default_filter)
	if args.km:
		kml.units = 'km'
	kml.write(collector.ways, path, basename)
	
	if args.add_kml is not None:
		for opt_string in args.add_kml:
			colorize = args.colorize
			filter = copy.copy(default_filter)
			opts = opt_string.split(',')
			for opt in opts:
				opt = opt.split('=')
				key = opt[0]
				if len(opt) < 2:
					sys.stderr.write("Key '{}' passed to --add_kml has no value, ignoring.\n".format(key))
					continue
				value = opt[1]
				if key == 'colorize':
					if int(value):
						colorize = 1
					else:
						colorize = 0
				elif key == 'min_curvature':
					filter.min_curvature = float(value)
				elif key == 'max_curvature':
					filter.max_curvature = float(value)
				elif key == 'min_length':
					filter.min_length = float(value)
				elif key == 'max_length':
					filter.max_length = float(value)
				else:
					sys.stderr.write("Ignoring unknown key '{}' passed to --add_kml\n".format(key))
			
			if colorize:
				kml = MultiColorKmlOutput(filter)
			else:
				kml = SingleColorKmlOutput(filter)
			if args.km:
				kml.units = 'km'
			kml.write(collector.ways, path, basename)
	
if args.v:
	sys.stderr.write("done.\n")

