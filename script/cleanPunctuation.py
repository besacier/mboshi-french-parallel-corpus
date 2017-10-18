import sys
import codecs
import glob

dir = sys.argv[1] #e.g. train/

def noPunctFile(inputName, outputName):
	with codecs.open(inputName,"r","UTF-8") as inputFile:
		with codecs.open(outputName, "w", "UTF-8") as outputFile:
			for line in inputFile:
				outputFile.write(line.replace(",","").replace("!","").replace(".","").replace("?",""))

trainFiles = glob.glob(sys.argv[1]+"*.fr.cleaned")

for fileName in trainFiles:
    noPunctFile(fileName, fileName + ".noPunct")
