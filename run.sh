#mv hawaii-main-island.c_0.l_0.kml kawaii-keep.kml
#python hillmapper-v2.py -v --max_lat_bound 20.31 --min_lat_bound 18.4 --min_lon_bound -156.38 --max_lon_bound -154.31 --output_basename hawaii-main-island --min_slope 0.1 --longest_road 4 ../hawaii-latest.osm
#mv hawaii-main-island.c_0.l_0.kml hawaii-main-island-testing.c_0.l_0.kml
#mv kawaii-keep.kml  hawaii-main-island.c_0.l_0.kml 
#sh upload.sh

python hillmapper-v2.py -v --max_lat_bound 43.2 --min_lat_bound 43.0 --min_lon_bound -89.6 --max_lon_bound -89.2 --output_basename madison-metropolis-area --longest_road 5 --min_slope 0.05 ../wisconsin-latest.osm

#madison: --max_lat_bound 43.16 --min_lat_bound 43.0 --min_lon_bound -89.63 --max_lon_bound -89.225
#kawaii hawaii: --max_lat_bound 22.31 --min_lat_bound 18.4 --min_lon_bound -160.38 --max_lon_bound -154.31