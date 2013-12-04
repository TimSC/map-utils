
#ogr2ogr -f "GeoJSON" mon.json 20131030_ScheduledMonument.shp 20131030_ScheduledMonument

import json, bz2, sys, os, string
from ostn02python import OSTN02, OSGB
from xml.sax.saxutils import escape, quoteattr

idpos = -1

class OSTN02Err(Exception):
	def __init__(self, message):

		# Call the base class constructor with the parameters it needs
		Exception.__init__(self, message)

def ConvertPoint(pt):
	try:
		(x,y,h) = OSTN02.OSGB36_to_ETRS89 (*pt)
		(gla, glo) = OSGB.grid_to_ll(x, y)
		return gla, glo
	except:
		print "OSTN02 not valid at", pt
		raise OSTN02Err("OSTN02 not valid at position")

def ConvertPolygon(rings):
	rings2 = []
	for ring in rings:
		ring2 = []
		for pt in ring:
			try:
				(x,y,h) = OSTN02.OSGB36_to_ETRS89 (*pt)
				(gla, glo) = OSGB.grid_to_ll(x, y)
			except:
				print "OSTN02 not valid at", pt
				raise OSTN02Err("OSTN02 not valid at position")

			#print pt, gla, glo

			ring2.append((gla, glo))

		rings2.append(ring2)
	return rings2

def ConvertMultiPolygon(polys):
	out = []
	for poly in polys:
		cp = ConvertPolygon(poly)
		out.append(cp)
	return out

def WriteClosedWay(poly, tags, outFi, nextIds):
	nodes = []
	for pt in poly[0]:
		nodes.append(nextIds['node'])
		outFi.write("<node id='{0}' lat='{1}' lon='{2}'></node>\n".format(nextIds['node'], pt[0], pt[1]))
		nextIds['node'] += idpos
	
	wid = nextIds['way']		
	outFi.write("<way id='{0}'>\n".format(wid))
	for nd in nodes[:-1]:
		outFi.write("<nd ref='{0}'/>\n".format(nd))
	outFi.write("<nd ref='{0}'/>\n".format(nodes[0]))
	
	for k in tags:
		outFi.write("<tag k={0} v={1}/>\n".format(quoteattr(unicode(escape(k))), quoteattr(escape(unicode(tags[k])))).encode("utf-8"))
	outFi.write("</way>\n")
	nextIds['way'] += idpos
	return wid

def PolyToOsm(poly, outFi, nextIds, tags):
	if len(poly)==1:
		
		WriteClosedWay(poly, tags, outFi, nextIds)
	else:
		wids = []
		for lineLoop in poly:
			wid = WriteClosedWay([lineLoop], {}, outFi, nextIds)
			wids.append(wid)
		
		outFi.write("<relation id='{0}'>\n".format(nextIds['relation']))
		for i, wid in enumerate(wids):
			role = "inner"
			if i == 0: role = "outer"
			outFi.write("<member type='{0}' ref='{1}' role={2}/>\n".format("way", wid, quoteattr(escape(role))))

		for k in tags:
			outFi.write(unicode("<tag k={0} v={1}/>\n").format(quoteattr(escape(unicode(k))), quoteattr(escape(unicode(tags[k])))).encode("utf-8"))
		outFi.write("<tag k='type' v='multipolygon'/>\n")
		outFi.write("</relation>\n")
		nextIds['relation'] += idpos

def MultiPolyToOsm(multipoly, outFi, nextIds, tags):
	outerWids = []
	innerWids = []
	for poly in multipoly:
		for i, lineLoop in enumerate(poly):
			wid = WriteClosedWay([lineLoop], {}, outFi, nextIds)
			if i == 0: outerWids.append(wid)
			else: innerWids.append(wid)

	outFi.write("<relation id='{0}'>\n".format(nextIds['relation']))
	for i, wid in enumerate(innerWids):
		role = "inner"
		outFi.write("<member type='{0}' ref='{1}' role={2}/>\n".format("way", wid, quoteattr(escape(role))))
	for i, wid in enumerate(outerWids):
		role = "outer"
		outFi.write("<member type='{0}' ref='{1}' role={2}/>\n".format("way", wid, quoteattr(escape(role))))

	for k in tags:
		outFi.write(unicode("<tag k={0} v={1}/>\n").format(quoteattr(escape(unicode(k))), quoteattr(escape(unicode(tags[k])))).encode("utf-8"))
	outFi.write("<tag k='type' v='multipolygon'/>\n")
	outFi.write("</relation>\n")
	nextIds['relation'] += idpos

def PointToOsm(pt, outFi, nextIds, tags):
	outFi.write("<node id='{0}' lat='{1}' lon='{2}'>\n".format(nextIds['node'], pt[0], pt[1]))
	for k in tags:
		outFi.write(unicode("<tag k={0} v={1}/>\n").format(quoteattr(escape(unicode(k))), quoteattr(escape(unicode(tags[k])))).encode("utf-8"))
	outFi.write("</node>\n")
	nextIds['node'] += idpos

def ConvertTags(tags):
	out = {}

	if 0:
		out['name'] = tags['Name']
		out['source'] = 'english_heritage_opendata'
		out['leisure'] = "garden"
		out['scheduled_monument:id'] = unicode(tags['ListEntry'])

	if 1:
		out['name'] = string.capwords(unicode(tags['Name']))
		out['source'] = 'english_heritage_opendata'
		out['building'] = 'yes'
		out['position_verified'] = 'no'
		out['listed_building'] = unicode(tags['Grade'])
		out['listed_building:ref'] = unicode(tags['ListEntry'])

	return out

if __name__ == "__main__":
	fina = "mon.json"
	finaOut = "out.osm.bz2"
	if len(sys.argv)>=2:
		fina = sys.argv[1]
	if len(sys.argv)>=3:
		finaOut = sys.argv[2]

	psl = os.path.splitext(fina)
	if psl[-1] == ".bz2":
		data = json.load(bz2.BZ2File(fina, "r"))
	else:
		data = json.load(open(fina))

	ty = data['type']
	print ty

	features = data['features']
	#outFi = open("out.osm", "wt")
	outFi = bz2.BZ2File(finaOut, "w")

	nextIds = {'node':idpos, 'way':idpos, 'relation':idpos}

	outFi.write("<?xml version='1.0' encoding='UTF-8'?>\n")
	outFi.write("<osm version='0.6' generator='py'>\n")

	for i, feature in enumerate(features):
		#if i > 500: continue		


		geometry = feature['geometry']
		feattype = feature['type']
		properties = feature['properties']

		#for featKey in feature:
		#	print featKey, feature[featKey]
		geometryType = geometry['type']
		geometryPts = geometry['coordinates']

		print i, len(features)
		#if geometryType == "MultiPolygon":
		print i, geometryType, len(geometryPts), properties
		#if len(geometryPts) != 1:
		#	print geometryType, len(geometryPts), properties

			#for geo in geometryPts:
			#	print geo

		if geometryType == "Point":
			try:
				pt = ConvertPoint(geometryPts)
				tagsConv = ConvertTags(properties)
				PointToOsm(pt, outFi, nextIds, tagsConv)
			except OSTN02Err as err:
				print "Conversion problem found", err

		if geometryType == "Polygon":
			try:
				poly = ConvertPolygon(geometryPts)
				tagsConv = ConvertTags(properties)
				PolyToOsm(poly, outFi, nextIds, tagsConv)
			except OSTN02Err as err:
				print "Conversion problem found", err

		if geometryType == "MultiPolygon":
			try:
				multipoly = ConvertMultiPolygon(geometryPts)
				tagsConv = ConvertTags(properties)
				MultiPolyToOsm(multipoly, outFi, nextIds, tagsConv)
			except OSTN02Err as err:
				print "Conversion problem found", err


		#print feattype, properties
	
	outFi.write("</osm>\n")
	outFi.close()
