#!/usr/bin/python -O

import xml2dict
import pprint

if __name__ == "__main__":
	tree    = xml2dict.ElementTree.parse('allappion.xml')
	root    = tree.getroot()
	xmldict = xml2dict.XmlDictConfig(root)
	pprint.pprint(xmldict)
