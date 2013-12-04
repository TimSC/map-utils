
#Extract a small area from an OSM file
#by Tim Sheerman-Chase, 2013
#You may reuse this file under the terms of CC0
#https://creativecommons.org/publicdomain/zero/1.0/

import pickle, bz2, sys
import trimutils

if __name__=="__main__":
	#fi = open('out.osm',"rt")

	finaIn = "surreyboundary.osm.bz2"
	if len(sys.argv) >= 2:
		finaIn = sys.argv[1]

	fi = bz2.BZ2File(finaIn,"r")

	roi = [51.072,51.472], [-0.850,0.040] #Surrey
	#roi = [50.7217072, 51.1475977], [-0.1424041, 0.8675128] #East sussex
	#[50.705752, 51.383075], [-1.955713,-0.729294] #Hampshire
	#[50.51865087505076,50.77226494056972], [-1.6009003235343708,-1.046058247973109] #Isle of wight
	#[50.703, 51.167], [-0.955, 0.040] #West sussex
	#roi = [51.825546373, 52.395492137], [-3.1428893, -2.3384747] #Herefordshire
	#roi = [50.201294, 51.245974], [-4.569239, -2.886625] #Devon

	#Find nodes in area of interest
	print "Finding nodes"
	if 1:
		roiNodes = trimutils.RoiNodes()
		roiNodes.SetRoiRect(roi)
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
	writeOutput.roi = roi
	writeOutput.ParseFile(fi)
	outfi.close()
	
