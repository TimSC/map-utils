
#Extract a small area from an OSM file
#by Tim Sheerman-Chase, 2013
#You may reuse this file under the terms of CC0
#https://creativecommons.org/publicdomain/zero/1.0/

import xml.parsers.expat as expat
import pickle, bz2
from xml.sax.saxutils import escape, quoteattr

class ExpatParse(object):
	def __init__(self):
		self.parser = expat.ParserCreate()
		self.parser.CharacterDataHandler = self.HandleCharData
		self.parser.StartElementHandler = self.HandleStartElement
		self.parser.EndElementHandler = self.HandleEndElement
		self.depth = 0
		self.tags = []
		self.attr = []

	def ParseFile(self, fi):
		fi.seek(0)
		self.parser.ParseFile(fi)

	def HandleCharData(self, data):
		pass

	def HandleStartElement(self, name, attrs):
		self.depth += 1
		self.tags.append(name)
		self.attr.append(attrs)

	def HandleEndElement(self, name): 
		self.depth -= 1
		self.tags.pop()
		self.attr.pop()

class RoiNodes(ExpatParse):
	def __init__(self):
		ExpatParse.__init__(self)
		self.roi = [51.072,51.472], [-0.850,0.040]
		self.objTypeCount = {'node':0, 'way':0, 'relation':0, 'changeset':0}
		self.objCount = 0
		self.foundNodes = set()

	def HandleStartElement(self, name, attrs):
		ExpatParse.HandleStartElement(self, name, attrs)
		assert self.depth < 4
		if self.depth == 2:
			if name in self.objTypeCount:
				self.objTypeCount[name] += 1
				self.objCount += 1
				if self.objCount % 100000==0:
					print self.objTypeCount, len(self.foundNodes)

		if self.depth == 2 and name == "node":
			lat = float(attrs['lat'])
			lon = float(attrs['lon'])
			if lat >= self.roi[0][0] \
				and lat <= self.roi[0][1] \
				and lon >= self.roi[1][0] \
				and lon <= self.roi[1][1]:
				self.foundNodes.add(int(attrs['id']))

	def HandleEndElement(self, name): 
		ExpatParse.HandleEndElement(self, name)

class RoiWays(ExpatParse):
	def __init__(self):
		ExpatParse.__init__(self)
		self.roiNodes = set()
		self.objTypeCount = {'node':0, 'way':0, 'relation':0, 'changeset':0}
		self.objCount = 0
		self.foundWays = set()
		self.wayNids = set()
		self.wayHit = 0
		self.referencesNodes = set()
		self.objTypeTotal = None

	def HandleStartElement(self, name, attrs):
		ExpatParse.HandleStartElement(self, name, attrs)
		assert self.depth < 4
		if self.depth == 2:
			if name in self.objTypeCount:
				self.objTypeCount[name] += 1
				self.objCount += 1
				if self.objCount % 100000==0:
					if self.objTypeTotal is not None:
						objDone = sum(self.objTypeCount.values())
						objTotal = sum(self.objTypeTotal.values())
						progress = float(objDone) / objTotal
						print progress, 
					print "w", self.objTypeCount, len(self.foundWays), len(self.referencesNodes)
			self.wayNids = set()
			self.wayHit = 0

		if self.depth == 3 and self.tags[1] == "way" and self.tags[2] == "nd":
			nid = int(attrs['ref'])
			self.wayNids.add(nid)
			if nid in self.roiNodes:
				self.wayHit = 1

	def HandleEndElement(self, name): 
		if self.depth == 2:
			if self.wayHit:
				self.foundWays.add(int(self.attr[1]['id']))
				self.referencesNodes.update(self.wayNids)

		ExpatParse.HandleEndElement(self, name)

class RoiRelations(ExpatParse):
	def __init__(self):
		ExpatParse.__init__(self)
		self.roiNodes = set()
		self.roiWays = set()
		self.objTypeCount = {'node':0, 'way':0, 'relation':0, 'changeset':0}
		self.objCount = 0
		self.foundRelations = set()
		self.objTypeTotal = None

	def HandleStartElement(self, name, attrs):
		ExpatParse.HandleStartElement(self, name, attrs)
		assert self.depth < 4
		if self.depth == 2:
			if name in self.objTypeCount:
				self.objTypeCount[name] += 1
				self.objCount += 1
				if self.objCount % 100000==0:
					if self.objTypeTotal is not None:
						objDone = sum(self.objTypeCount.values())
						objTotal = sum(self.objTypeTotal.values())
						progress = float(objDone) / objTotal
						print progress, 

					print "r", self.objTypeCount, len(self.foundRelations)

		if self.depth == 3 and self.tags[1] == "relation" and self.tags[2] == "member":
			nid = int(attrs['ref'])
			ty = attrs['type']
			if ty == "node" and nid in self.roiNodes:
				self.foundRelations.add(int(self.attr[1]['id']))
			if ty == "way" and nid in self.roiWays:
				self.foundRelations.add(int(self.attr[1]['id']))

	def HandleEndElement(self, name): 
		ExpatParse.HandleEndElement(self, name)


class WriteOutput(ExpatParse):
	def __init__(self, fina):
		ExpatParse.__init__(self)
		self.roiNodes = set()
		self.roiWays = set()
		self.roiRelations = set()
		self.objTypeCount = {'node':0, 'way':0, 'relation':0, 'changeset':0}
		self.objCount = 0
		self.skip = 0
		self.roi = None
		self.objTypeTotal = None
		self.missingMem = 0

		if isinstance(fina, basestring):
			self.fi = open(fina, "wt")
		else:
			self.fi = fina
		self.fi.write("<?xml version='1.0' encoding='UTF-8'?>\n")
	
	def HandleCharData(self, data):
		pass

	def HandleStartElement(self, name, attrs):
		ExpatParse.HandleStartElement(self, name, attrs)
		assert self.depth < 4

		if self.depth == 2:
			if name in self.objTypeCount:
				self.objTypeCount[name] += 1
				self.objCount += 1
				if self.objCount % 100000==0:
					if self.objTypeTotal is not None:
						objDone = sum(self.objTypeCount.values())
						objTotal = sum(self.objTypeTotal.values())
						progress = float(objDone) / objTotal
						print progress, 

					print "o", self.objTypeCount

			self.skip = 1
			if "id" in attrs:
				objId = int(attrs['id'])
				if name=="node" and objId in self.roiNodes:
					self.skip = 0
				if name=="way" and objId in self.roiWays:
					self.skip = 0
				if name=="relation" and objId in self.roiRelations:
					self.skip = 0

		#Prevent incomplete relations with negative ids
		if not self.skip and self.depth == 3 and self.tags[1]=="relation" and name == "member":
			self.missingMem = 0
			objId = int(self.attr[1]['id'])
			nid = int(attrs['ref'])
			ty = attrs['type']
			if objId < 0 and ty == "node" and nid not in self.roiNodes: self.missingMem = 1
			if objId < 0 and ty == "way" and nid not in self.roiWays: self.missingMem = 1
			if objId < 0 and ty == "relation" and nid not in self.roiRelations: self.missingMem = 1

		if not self.skip and not self.missingMem:
			openTag = "<"+name
			for k in attrs:
				openTag += " "+k+"="+quoteattr(escape(str(attrs[k])))
			openTag += ">\n"
			self.fi.write(openTag.encode("utf-8"))

		if self.depth == 1 and self.roi is not None:
			self.fi.write("<bounds minlat='{0}' minlon='{1}' maxlat='{2}' maxlon='{3}'/>\n" \
				.format(self.roi[0][0], self.roi[1][0], self.roi[0][1], self.roi[1][1]))


	def HandleEndElement(self, name): 
		if not self.skip and not self.missingMem:
			closeTag = "</"+name+">\n"
			self.fi.write(closeTag.encode("utf-8"))

		if self.depth <= 2:
			self.skip = 0

		if self.depth <= 3:
			self.missingMem = 0

		ExpatParse.HandleEndElement(self, name)	

if __name__=="__main__":
	#fi = open('out.osm',"rt")
	fi = bz2.BZ2File("/media/noraid/tim/planet-130327-recomp.osm.bz2","r")

	roi = [0.,90.], [-180.,0.]

	#Find nodes in area of interest
	print "Finding nodes"
	if 1:
		roiNodes = RoiNodes()
		roiNodes.roi = roi
		roiNodes.ParseFile(fi)
		foundNodes = roiNodes.foundNodes
		objTypeCount = roiNodes.objTypeCount
		pickle.dump(foundNodes, open("foundNodes.bin","wb"), protocol=-1)
		pickle.dump(objTypeCount, open("objTypeCount.bin","wb"), protocol=-1)
		del roiNodes
	else:
		foundNodes = pickle.load(open("foundNodes.bin","rb"))
		objTypeCount = pickle.load(open("objTypeCount.bin","rb"))

	#Find ways that reference ROI nodes
	print "Finding ways"
	if 1:
		roiWays = RoiWays()
		roiWays.roiNodes = foundNodes
		roiWays.objTypeTotal = objTypeCount
		roiWays.ParseFile(fi)
		foundWays = roiWays.foundWays
		referencesNodes = roiWays.referencesNodes
		pickle.dump(foundWays, open("foundWays.bin","wb"), protocol=-1)
		pickle.dump(referencesNodes, open("referencesNodes.bin","wb"), protocol=-1)
		del roiWays
		del foundNodes
	else:
		foundWays = pickle.load(open("foundWays.bin","rb"))
		referencesNodes = pickle.load(open("referencesNodes.bin","rb"))

	#Get relations that reference ROI objects
	print "Find relations"
	if 1:
		roiRelations = RoiRelations()
		roiRelations.roiNodes = referencesNodes
		roiRelations.roiWays = foundWays
		roiRelations.objTypeTotal = objTypeCount
		roiRelations.ParseFile(fi)
		foundRelations = roiRelations.foundRelations
		pickle.dump(foundRelations, open("foundRelations.bin","wb"), protocol=-1)
		del roiRelations
	else:
		foundRelations = pickle.load(open("foundRelations.bin","rb"))

	#Write output
	print "Write output"
	outfi = bz2.BZ2File("/media/noraid/tim/planet-130327-recomp.osm.bz2", "w")
	writeOutput = WriteOutput(outfi)
	writeOutput.roiNodes = referencesNodes
	writeOutput.roiWays = foundWays	
	writeOutput.roiRelations = foundRelations
	writeOutput.objTypeTotal = objTypeCount
	writeOutput.roi = roi
	writeOutput.ParseFile(fi)
	outfi.close()
	
