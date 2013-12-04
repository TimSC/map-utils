
import osmtoshapely, bz2
import xml.etree.ElementTree as ET

#1000000029462 #Surrey
#172385 #Kent
#172799 #Hampshire
#92650 #E Sussex

if __name__=="__main__":
	newObjsXml = bz2.BZ2File("surreyboundary.osm.bz2", "r").read()
	root = ET.fromstring(newObjsXml)
	outObjs = osmtoshapely.OsmToShapely(root)

	closedObjs = []
	for obj in outObjs:
		if obj[0].geom_type not in ["Polygon", "MultiPolygon"]: continue
		closedObjs.append(obj)

	print closedObjs

