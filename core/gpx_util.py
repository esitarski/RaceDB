import sys
import numpy as np
from xml import sax
from xml.sax.saxutils import escape
from math import sqrt, sin, cos, radians, atan2
from functools import partial

def lat_lon_elevation_from_gpx( gpx ):
	
	class GPXTrackHandler( sax.handler.ContentHandler ):
		def __init__( self, *args, **kwargs ):
			super().__init__( *args, **kwargs )
			self.reset()
			
		def reset( self ):
			self.lat_lon_elevation = []
			self.lat = self.lon = self.elevation = 0.0
			self.in_ele = 0
		
		def startElement( self, name, attrs ):
			if name == 'trkpt':
				self.lat, self.lon = float(attrs['lat'].strip()), float(attrs['lon'].strip())
			elif name == 'ele':
				self.in_ele += 1
			elif name == 'trkseg':
				self.reset()
				
		def characters( self, content ):
			if self.in_ele:
				self.elevation = float(content.strip())
	
		def endElement( self, name ):
			if name == 'ele':
				self.in_ele -= 1
			elif name == 'trkpt':
				self.lat_lon_elevation.append( (self.lat, self.lon, self.elevation) )
				
	p = sax.make_parser()
	gth = GPXTrackHandler()
	p.setContentHandler( gth )
	try:
		p.parse( gpx )
	except Exception as e:
		return []

	return gth.lat_lon_elevation
	
def lat_lon_elevation_to_gpx( lat_lon_elevation, stream=None, name="" ):
	stream = stream or sys.stdout
	
	stream.write( """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.0"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	creator="Edward Sitarski lat_lon_elevation_to_gpx"
	xmlns="http://www.topografix.com/GPX/1/0"
	xsi:schemaLocation="http://www.topografix.com/GPX/1/0 http://www.topografix.com/GPX/1/0/gpx.xsd">
"""
	)
	stream.write( '<trk>\n' )
	if name:
		stream.write( '<name>{}</name>'.format(escape(name)) )
	stream.write( '<trkseg>\n' )
	for lat, lon, e in lat_lon_elevation:
		stream.write( '<trkpt lat="{}" lon="{}"><ele>{}</ele></trkpt>\n'.format(lat, lon, e) )
	stream.write( '</trkseg>\n' )
	stream.write( '</trk>\n' )
	stream.write( '</gpx>\n' )

def great_circle_distance( pointA, pointB ):
	EARTH_RADIUS = 6371.0088 * 1000.0	# meters

	latA, lonA = (float(i) for i in pointA)
	latB, lonB = (float(i) for i in pointB)
	phiA = radians( latA )
	phiB = radians( latB )
	delta_latitude = radians(latB - latA)
	delta_longitude = radians(lonB - lonA)
	a = (
		sin(delta_latitude / 2.0) ** 2
		+ cos(phiA) * cos(phiB) * sin(delta_longitude / 2.0) ** 2
	)
	c = 2.0 * atan2(sqrt(a), sqrt(max(0.0, 1.0 - a)))
	return EARTH_RADIUS * c

def pldist( point, start, end ):
	"""
	Calculate the distance from point to the line.
	All points are numpy arrays.
	"""
	if np.array_equal(start, end):
		return np.linalg.norm(point - start)

	delta_line = end - start
	return np.divide(
		np.abs(np.linalg.norm(np.cross(delta_line, start - point))),
		np.linalg.norm(delta_line)
	)

def _rdp_iter(M, start_index, last_index, epsilon, dist=pldist):
	stk = [(start_index, last_index)]
	global_start_index = start_index
	mask = np.ones(last_index - start_index + 1, dtype=bool)

	while stk:
		start_index, last_index = stk.pop()

		dmax = 0.0
		index = start_index
		
		p1, p2 = M[start_index], M[last_index]

		for i in range(index + 1, last_index):
			if mask[i - global_start_index]:
				d = dist(M[i], p1, p2)
				if d > dmax:
					index = i
					dmax = d

		if dmax > epsilon:
			stk.append((start_index, index))
			stk.append((index, last_index))
		else:
			mask[start_index + 1 - global_start_index:last_index - global_start_index] = False

	return mask

def rdp_iter(M, epsilon, dist=pldist, return_mask=False):
	"""
		Simplifies a given array of points (multi-dimensional).
		return_mask: return the mask of points to keep instead of the edited points.
	"""
	mask = _rdp_iter(M, 0, len(M) - 1, epsilon, dist)

	if return_mask:
		return mask

	return M[mask]

def rdp(M, epsilon=0, dist=pldist, return_mask=False):
	"""
		Simplifies a given array of points M using the Ramer-Douglas-Peucker
		algorithm.
	"""

	algo = partial(rdp_iter, return_mask=return_mask)
		
	if "numpy" in str(type(M)):
		return algo(M, epsilon, dist)

	return algo(np.array(M), epsilon, dist).tolist()

def lat_lon_elevation_to_points_itr( lat_lon_elevation ):
	lat_min = lat_max = lat_lon_elevation[0][0]
	lon_min = lon_max = lat_lon_elevation[0][1]
	for lat, lon, e in lat_lon_elevation:
		if lat < lat_min:
			lat_min = lat
		elif lat > lat_max:
			lat_max = lat
		if lon < lon_min:
			lon_min = lon
		elif lon > lon_max:
			lon_max = lon
	
	# Use a flat earth and compute the length of a degree.
	degree_delta = (lat_max - lat_min) / 5.0
	lat_distance = great_circle_distance( (lat_min, lon_min), (lat_min+degree_delta, lon_min) ) / degree_delta
	degree_delta = (lon_max - lon_min) / 5.0
	lon_distance = great_circle_distance( (lat_min, lon_min), (lat_min, lon_min+degree_delta) ) / degree_delta
	
	# Multiply the length of the lat, lon difference.
	return ( ((lat - lat_min) * lat_distance, (lon - lon_min) * lon_distance, e) for (lat, lon, e) in lat_lon_elevation )

def simplify_gpx_file( gpx, epsilon=1.0 ):
	lat_lon_elevation = lat_lon_elevation_from_gpx( gpx )
	
	points_itr = lat_lon_elevation_to_points_itr( lat_lon_elevation )
	p = np.fromiter( points_itr, dtype=np.dtype((float, 3)) )
	
	mask = rdp( p, epsilon, return_mask=True );
	lat_lon_elevation = [v for i, v in enumerate(lat_lon_elevation) if mask[i]]
	
	p = p[mask]
	return lat_lon_elevation, p		# Return the edited points and xy_elevation array.
	
if __name__ == '__main__':
	import json
	lat_lon_elevation, points = simplify_gpx_file( 'hero_dolomites_86_km_14_06_22.gpx' )
	with open('hero_dolomites_86_km_14_06_22_filter.gpx', 'w') as f:
		lat_lon_elevation_to_gpx( lat_lon_elevation, f )
	with open('hero_dolomites_86_km_14_06_22_filter.json', 'w') as f:
		json.dump( lat_lon_elevation, f )
	
