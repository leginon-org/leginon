#!/usr/bin/python -O

import apXml
import pprint

if __name__ == "__main__":
	function = "selexon"
	tree      = apXml.ElementTree.parse('allappion.xml')
	treeroot  = tree.getroot()
	xmldict   = apXml.XmlDictConfig(treeroot)

	tree     = apXml.ElementTree.parse(function+".xml")
	treeroot = tree.getroot()
	xmldict2 = apXml.XmlDictConfig(treeroot)

	for p in xmldict2:
		if p in xmldict:
			xmldict[p].update(xmldict2[p])
		else:
			xmldict[p] = xmldict2[p]

	xmldict   = apXml.updateXmlDict(xmldict)

	apXml.printHelp(xmldict)
	#pprint.pprint(xmldict)
