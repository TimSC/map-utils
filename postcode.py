import zipfile, csv
from ostn02python import OSGB, OSTN02

if __name__=="__main__":
	
	z = zipfile.ZipFile(open("/home/tim/Downloads/ONSPD_NOV_2013_csv.zip"), "r")
	#print z.namelist()
	data = z.open("Data/ONSPD_NOV_2013_UK.csv")

	data2 = csv.DictReader(data)
	skipDeleted = True
	count = 0

	#outfi = bz2.BZ2File("postcode.osm.bz2", "w")	

	if isinstance(fina, basestring):
		self.fi = open(fina, "wt")
	else:
		self.fi = fina
	self.fi.write("<?xml version='1.0' encoding='UTF-8'?>\n")

	for li in data2:
		if len(li['oseast1m']) == 0: continue
		e = float(li['oseast1m'])
		n = float(li['osnrth1m'])
		qual = int(li['osgrdind'])
		pcs = li['pcd']
		doterm = li['doterm']
		if len(doterm) > 0 and skipDeleted: continue


		try:
			(x,y,h) = OSTN02.OSGB36_to_ETRS89 (e, n)
			(gla, glo) = OSGB.grid_to_ll(x, y)
			print pcs, doterm, qual, gla, glo, count
			count += 1
		except:
			print pcs, "conversion failed"

