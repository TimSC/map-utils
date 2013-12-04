
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.geos import PredicateError
from shapely.validation import explain_validity

def WayToPoly(wayId, ways, nodes):
	wayData = ways[wayId]
	wayNodes = wayData[0]
	if wayNodes[0] == wayNodes[-1]:
		#Close polygon
		tags = wayData[1]
		pts = []
		for nid in wayNodes:
			if int(nid) not in nodes:
				print "Warning: missing node", nid
				continue
			pts.append(nodes[int(nid)][0])

		#Require at least 3 points
		if len(pts) < 3:
			return None

		poly = Polygon(pts)
		if not poly.is_valid:
			print "Warning: polygon is not valid"
			print explain_validity(poly)
			poly = poly.buffer(0)
		return poly
	else:
		#Unclosed way
		tags = wayData[1]
		pts = []
		for nid in wayNodes:
			if int(nid) not in nodes:
				print "Warning: missing node", nid
				continue
			pts.append(nodes[int(nid)][0])		

		line = LineString(pts)
		if not line.is_valid:
			print "Warning: polygon is not valid"
			print explain_validity(line)
			line = line.buffer(0)
		return line

	return None	

def MergePolySections(sections):
	#Merge way fragments into closed polygons
	merging = True
	
	while merging:
		l1, l2 = None, None
		m1, m2 = None, None
		for wayNum, way in enumerate(sections):
			if way.geom_type != "LineString": continue
			#print wayNum, way.geom_type, way.coords[0], way.coords[-1]
		
			for wayNum2, way2 in enumerate(sections):
				if wayNum == wayNum2: continue

				if way.coords[0] == way2.coords[0]:
					l1 = way.coords[::-1]
					l2 = way2.coords[:]
				if way.coords[0] == way2.coords[-1]:
					l1 = way.coords[::-1]
					l2 = way2.coords[::-1]
				if way.coords[-1] == way2.coords[0]:
					l1 = way.coords[:]
					l2 = way2.coords[:]
				if way.coords[-1] == way2.coords[-1]:
					l1 = way.coords[:]
					l2 = way2.coords[::-1]

				if l1 is not None: 
					m1 = wayNum
					m2 = wayNum2
					break
			if l1 is not None: break

		if l1 is not None:
			#print "Merging", wayNum, "with", wayNum2
			if l1[0] == l2[-1]:
				#Closed
				mg = Polygon(l1+l2[1:-1])
			else:
				#Unclosed
				mg = LineString(l1+l2[1:])

			#Filter remaining
			filtSections = []
			for wayNum, way in enumerate(sections):
				if wayNum in [m1, m2]: continue
				filtSections.append(way)

			#Add merged section
			filtSections.append(mg)

			sections = filtSections

		else:
			merging = False

	return sections

def RelationToPoly(relId, ways, nodes, relations):
	members = relations[relId][0]
	tags = relations[relId][1]

	#Check tags
	if "type" not in tags: return None
	if tags['type'] not in ["multipolygon", "boundary"]: return None

	outerPolys = []
	innerPolys = []
	for mem in members:	
		if mem['role'] == "outer":
			ref = int(mem['ref'])
			if ref in ways:
				poly = WayToPoly(ref, ways, nodes)
				if poly is None: continue
				outerPolys.append(poly)
		if mem['role'] == "inner":
			ref = int(mem['ref'])
			if ref in ways:
				poly = WayToPoly(ref, ways, nodes)
				if poly is None: continue
				innerPolys.append(poly)

	#Join sections of outer polygons to form longer chain
	outerPolys = MergePolySections(outerPolys)
	innerPolys = MergePolySections(innerPolys)

	#Force outer polygons to be closed?
	#TODO

	#Match internal polygons with outer polygon
	outerPolyRings = []
	for outerPoly in outerPolys:

		matchingInteriorPolys = []
		for inPol in innerPolys:
			if outerPoly.contains(inPol):
				if isinstance(inPol, Polygon):
					matchingInteriorPolys.append(inPol.exterior.coords)
				else:
					for ply in inPol.geoms:
						matchingInteriorPolys.append(ply.exterior.coords)

		if isinstance(outerPoly, MultiPolygon):
			for ply in outerPoly.geoms:
				outerPolyRings.append((ply.exterior.coords, matchingInteriorPolys))
		if isinstance(outerPoly, Polygon):
			outerPolyRings.append((outerPoly.exterior.coords, matchingInteriorPolys))

	if len(outerPolyRings) > 0:
		return MultiPolygon(outerPolyRings)
	return None

def ParseOsmToObjs(root):
	nodes = {}
	ways = {}
	relations = {}
	for child in root:
		tags = {}
		if child.tag == "node":
			for mem in child:
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			nodes[int(child.attrib['id'])] = [map(float, [child.attrib['lat'], child.attrib['lon']]), tags, child.attrib]

		if child.tag == "way":
			memNodes = []
			for mem in child:
				#print mem.tag, mem.attrib
				if mem.tag == "nd":
					memNodes.append(int(mem.attrib['ref']))
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			ways[int(child.attrib['id'])] = [memNodes, tags, child.attrib]

		if child.tag == "relation":
			memObjs = []
			for mem in child:
				#print mem.tag, mem.attrib
				if mem.tag == "member":
					memObjs.append(mem.attrib)
				if mem.tag == "tag":
					tags[mem.attrib['k']] = mem.attrib['v']

			relations[int(child.attrib['id'])] = [memObjs, tags, child.attrib]

		#print child.tag, child.attrib
	#print ways
	return nodes, ways, relations

def OsmToShapely(root):
	nodes, ways, relations = ParseOsmToObjs(root)

	outObjs = []
	for wayId in ways:
		poly = WayToPoly(wayId, ways, nodes)
		if poly is None: continue
		tags = ways[wayId][1]

		outObjs.append((poly, "way", wayId, tags))

	for relId in relations:
		rel = RelationToPoly(relId, ways, nodes, relations)
		if rel is None: continue
		tags = relations[relId][1]

		outObjs.append((rel, "relation", relId, tags))

	return outObjs


