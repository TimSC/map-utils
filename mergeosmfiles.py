import bz2, os, sys
import xml.etree.ElementTree as ET

def MergeFile(fina, ty, nextObjId, idMapping, fiOut):
	fes = os.path.splitext(fina)
	if fes[-1] == ".bz2":
		fi = bz2.BZ2File(fina, "r")
	else:
		fi = open(fina, "rt")

	root = ET.fromstring(fi.read())

	if fina not in idMapping:
		idMapping[fina] = {}
	fiMapping = idMapping[fina]

	if ty not in fiMapping:
		fiMapping[ty] = {}
	tyMapping = fiMapping[ty]
	ndMapping = fiMapping['node']

	for el in root:
		if el.tag != ty: continue
		oldId = el.attrib['id']
		tyMapping[oldId] = str(nextObjId[ty])
		nextObjId[ty] -= 1

		el.attrib['id'] = tyMapping[oldId]
		print el.tag, el.attrib['id']

		for ch in el:
			if ch.tag=="nd":
				#print ch.tag, ch.attrib
				#print "Remap node", ch.attrib['ref'], "to", ndMapping[ch.attrib['ref']]
				ch.attrib['ref'] = ndMapping[ch.attrib['ref']]
			if ch.tag=="member":
				assert(0)#Not implemented

		xml = ET.tostring(el, encoding="utf-8")
		fiOut.write(xml)

if __name__=="__main__":
	
	out = bz2.BZ2File("merge.osm.bz2","w")
	#out = open("merge.osm","wt")
	out.write("<?xml version='1.0' encoding='UTF-8'?>\n")
	out.write("<osm version='0.6' generator='py'>\n")

	fiList = sys.argv[1:]
	
	nextObjId = {"node": -1, "way": -1, "relation": -1}
	idMapping = {}

	for fina in fiList:
		MergeFile(fina, "node", nextObjId, idMapping, out)

	for fina in fiList:
		MergeFile(fina, "way", nextObjId, idMapping, out)

	for fina in fiList:
		MergeFile(fina, "relation", nextObjId, idMapping, out)

	out.write("</osm>\n")
	out.close()


