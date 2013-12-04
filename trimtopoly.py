#Extract a small area from an OSM file
#by Tim Sheerman-Chase, 2013
#You may reuse this file under the terms of CC0
#https://creativecommons.org/publicdomain/zero/1.0/

import osmtoshapely
import pickle, bz2, sys
import trimutils
import xml.etree.ElementTree as ET
import shapely.speedups as speedups

if __name__=="__main__":

	print "shapely speedups.available", speedups.available
	if speedups.available:
		speedups.enable()

	newObjsXml = bz2.BZ2File("surreyboundary.osm.bz2", "r").read()
	root = ET.fromstring(newObjsXml)
	outObjs = osmtoshapely.OsmToShapely(root)

	#Get user defined shape for trim
	boundingObj = None
	for obj in outObjs:
		#if obj[0].geom_type not in ["Polygon", "MultiPolygon"]: continue
		objTy = obj[1]
		objId = obj[2]
		if objTy=="relation" and objId==1000000029462: boundingObj = obj #Surrey
		#172385 #Kent
		#172799 #Hampshire
		#92650 #E Sussex

		if boundingObj is not None: break

	print "roi", boundingObj

	#Load data to trim
	finaIn = "surrey-fosm-dec-2013.osm.bz2"
	if len(sys.argv) >= 2:
		finaIn = sys.argv[1]

	fi = bz2.BZ2File(finaIn,"r")

	#Find nodes in area of interest
	print "Finding nodes"
	if 1:
		roiNodes = trimutils.RoiNodes()
		roiNodes.SetRoiShapely(boundingObj[0][0])
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
		roiWays = trimutils.RoiWays()
		roiWays.roiNodes = foundNodes
		roiWays.objTypeTotal = objTypeCount
		roiWays.ParseFile(fi)
		foundWays = roiWays.foundWays
		referencesNodes = roiWays.referencesNodes
		pickle.dump(foundWays, open("foundWays.bin","wb"), protocol=-1)
		pickle.dump(referencesNodes, open("referencesNodes.bin","wb"), protocol=-1)
		referencesNodes.update(foundNodes)
		del roiWays
		del foundNodes
	else:
		foundWays = pickle.load(open("foundWays.bin","rb"))
		referencesNodes = pickle.load(open("referencesNodes.bin","rb"))
		referencesNodes.update(foundNodes)

	#Get relations that reference ROI objects
	print "Find relations"
	if 1:
		roiRelations = trimutils.RoiRelations()
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
	outfi = bz2.BZ2File("out.osm.bz2", "w")
	writeOutput = trimutils.WriteOutput(outfi)
	writeOutput.roiNodes = referencesNodes
	writeOutput.roiWays = foundWays	
	writeOutput.roiRelations = foundRelations
	writeOutput.objTypeTotal = objTypeCount
	writeOutput.ParseFile(fi)
	outfi.close()
	
