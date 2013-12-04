import zipfile, csv, bz2
from ostn02python import OSGB, OSTN02

if __name__=="__main__":
	
	z = zipfile.ZipFile(open("/home/tim/Downloads/ONSPD_NOV_2013_csv.zip"), "r")
	#print z.namelist()
	data = z.open("Data/ONSPD_NOV_2013_UK.csv")

	data2 = csv.DictReader(data)
	skipDeleted = True
	count = 0
	nodeId = -1

	fina = bz2.BZ2File("postcode.osm.bz2", "w")	

	if isinstance(fina, basestring):
		fi = open(fina, "wt")
	else:
		fi = fina
	fi.write("<?xml version='1.0' encoding='UTF-8'?>\n")
	fi.write("<osm version='0.6' upload='true' generator='JOSM'>\n")

	for li in data2:
		if len(li['oseast1m']) == 0: continue
		e = float(li['oseast1m'])
		n = float(li['osnrth1m'])
		qual = int(li['osgrdind'])
		pcs = li['pcds']
		doterm = li['doterm']
		if len(doterm) > 0 and skipDeleted: continue

		try:
			(x,y,h) = OSTN02.OSGB36_to_ETRS89 (e, n)
			(gla, glo) = OSGB.grid_to_ll(x, y)
			if count % 100 == 0:
				print pcs, doterm, qual, gla, glo, count
			count += 1

			fi.write("<node id='{0}' lat='{1}' lon='{2}'>\n".format(nodeId, gla, glo))
			fi.write("<tag k='name' v='{0}' />\n".format(pcs))
			fi.write("<tag k='onspd_postcode_centre' v='yes' />\n")
			fi.write("</node>\n")

			nodeId -= 1

		except:
			print pcs, "conversion failed"

	fi.write("</osm>\n")
	fi.close()

