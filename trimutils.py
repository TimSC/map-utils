import xml.parsers.expat as expat
from xml.sax.saxutils import escape, quoteattr
from shapely.geometry import LineString, Polygon, MultiPolygon, Point
from shapely.geos import PredicateError
from shapely.validation import explain_validity
from shapely.prepared import prep

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
		self.fiTmp = fi
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
		if self.depth >= 4:
			print self.tags
			pos = self.fiTmp.tell()
			print "pos", pos
			print "attr", self.attr
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
			pt = Point((lat, lon))

			if self.roi.contains(pt):
				self.foundNodes.add(int(attrs['id']))

	def HandleEndElement(self, name): 
		ExpatParse.HandleEndElement(self, name)

	def SetRoiRect(self, rect):
		self.roi = Polygon([(rect[0][0], rect[1][0]), (rect[0][0], rect[1][1]), 
			(rect[0][1], rect[1][1]), (rect[0][1], rect[1][0])])

	def SetRoiShapely(self, shp):
		self.roi = prep(shp)

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
			openTag = unicode("<")+name
			for k in attrs:
				openTag += unicode(" ")+k+unicode("=")+quoteattr(escape(unicode(attrs[k])))
			openTag += unicode(">\n")
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
