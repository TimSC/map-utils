
import xml.etree.ElementTree as ET
import urllib2, pickle, sys

#http://www.fosm.org/api/0.6/*[natural=wood][bbox=-0.4387665,50.896104,-0.3240967,50.9657788]
#http://fosm.org/api/0.6/node/288550196/ways
#http://www.fosm.org/api/0.6/*[natural=wood][bbox=-0.955,50.703,0.040,51.167] #West sussex

#http://www.fosm.org/api/0.6/*[natural=wood][bbox=-0.850,51.072,0.040,51.472] #Surrey

#http://www.fosm.org/api/0.6/*[operator=rspb][bbox=-9.140625,49.6676278,2.4609375,61.0582854] #UK








def GetWayParents(objTy, objId):
	out = []
	if objTy == "node":
		url = "http://fosm.org/api/0.6/node/{0}/ways".format(objId)
		handle = urllib2.urlopen(url)
		root = ET.fromstring(handle.read())
		for obj in root:
			out.append(obj)
	return out

def GetRelationParents(objTy, objId):
	out = []
	url = "http://fosm.org/api/0.6/{0}/{1}/relations".format(objTy, objId)
	handle = urllib2.urlopen(url)
	root = ET.fromstring(handle.read())
	for obj in root:
		out.append(obj)

	return out

def InitKnownObjectIds(knownObjs):
	knownIds = {'node': set(), 'way': set(), 'relation': set()}

	#Copy known objects to list
	for obj in knownObjs:
		if obj.tag == "bounds": continue
		knownIds[obj.tag].add(int(obj.attrib['id']))
	return knownIds

if __name__=="__main__":

	inFiNa = 'woods.osm'
	outFiNa = 'out.osm'

	if len(sys.argv)>=1:
		inFiNa = sys.argv[1]
	if len(sys.argv)>=2:
		outFiNa = sys.argv[2]

	tree = ET.parse(inFiNa)
	knownObjs = []

	for obj in tree.getroot():
		if obj.tag == "bounds": continue
		knownObjs.append(obj)
	knownIds = InitKnownObjectIds(knownObjs)

	#Get way parents of objects
	for count, obj in enumerate(knownObjs):
		print "Get parent ways", count, len(knownObjs), obj.tag, obj.attrib
		parents = GetWayParents(obj.tag, int(obj.attrib['id']))
		for obj2 in parents:
			obj2id = int(obj2.attrib['id'])
			if obj2id not in knownIds[obj2.tag]:
				knownObjs.append(obj2)
				knownIds[obj.tag].add(obj2id)

	pickle.dump(knownObjs, open("knownObjs1.dat","wb"), protocol=-1)

	#Get relation parents of objects
	for count, obj in enumerate(knownObjs):
		print "Get parent relations", count, len(knownObjs), obj.tag, obj.attrib
		parents = GetRelationParents(obj.tag, int(obj.attrib['id']))
		for obj2 in parents:
			obj2id = int(obj2.attrib['id'])
			if obj2id not in knownIds[obj2.tag]:
				knownObjs.append(obj2)
				knownIds[obj.tag].add(obj2id)

	pickle.dump(knownObjs, open("knownObjs2.dat","wb"), protocol=-1)
	#knownObjs = pickle.load(open("knownObjs1.dat","rb"))
	#knownIds = InitKnownObjectIds(knownObjs)

	if 0:
		#Download nodes to complete ways
		for obj in knownObjs:
			if obj.tag != "way": continue

			for objch in obj:
				if objch.tag != "nd": continue
				nid = int(objch.attrib['ref'])
				if nid in knownIds['node']: continue
				url = "http://fosm.org/api/0.6/node/{0}".format(nid)
				print url
				handle = urllib2.urlopen(url)
				root = ET.fromstring(handle.read())
				for obj2 in root:
					obj2id = int(obj2.attrib['id'])
					if obj2id in knownIds[obj2.tag]:
						continue
					knownObjs.append(obj2)
					knownIds[obj2.tag].add(obj2id)

	pickle.dump(knownObjs, open("knownObjs3.dat","wb"), protocol=-1)
	#knownObjs = pickle.load(open("knownObjs2.dat","rb"))
	#knownIds = InitKnownObjectIds(knownObjs)
	
	#Write output
	out = open(outFiNa, "wt")
	
	out.write("<?xml version='1.0' encoding='UTF-8'?>\n")
	out.write("<osm version='0.6' generator='completeparents.py'>\n")

	for obj in knownObjs:
		if obj.tag != "node": continue
		xml = ET.tostring(obj, encoding="utf-8")
		out.write(xml)

	for obj in knownObjs:
		if obj.tag != "way": continue
		xml = ET.tostring(obj, encoding="utf-8")
		out.write(xml)

	for obj in knownObjs:
		if obj.tag != "relation": continue
		xml = ET.tostring(obj, encoding="utf-8")
		out.write(xml)

	out.write("</osm>\n")

