import sys
import re
import os
import xml.dom.minidom

#taken from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/409899
#Title: xmlreader2
#Submitter: Peter Neish (other recipes) 
#**HEAVILY** modified by Neil

def nodeToDict(node, listing_names=[]):
	"""
	nodeToDic() scans through the children of node and makes a
	dictionary from the content.
	two cases are differentiated:
	- if the node contains no other nodes, it is a text-node
	  and {nodeName:text} is merged into the dictionary.
	- else, nodeToDic() will call itself recursively on
	  the children nodes.
	Duplicate entries are overwritten
	"""
	xmldict = {}
	for n in node.childNodes:
		if n.nodeType != n.ELEMENT_NODE:
			continue
		text = False
		if len(n.childNodes) == 1 and n.childNodes[0].nodeType == n.TEXT_NODE:
			text = str(n.childNodes[0].nodeValue)
			if len(text) > 0:
				xmldict.update({str(n.nodeName): text})
			else:
				xmldict.update({str(n.nodeName): None})
		elif len(n.childNodes) > 0:
			if str(n.nodeName) not in listing_names:
				# This is a problem for multiple entries that needs to be in a list
				xmldict.update({str(n.nodeName): nodeToDict(n, listing_names)})
			else:
				if str(n.nodeName) in list(xmldict.keys()):
					if type(xmldict[str(n.nodeName)]) == type({}):
						xmldict[str(n.nodeName)] = [xmldict[str(n.nodeName)],]
				else:
					xmldict[str(n.nodeName)] = []
				xmldict[str(n.nodeName)].append(nodeToDict(n, listing_names))
	return xmldict

def readDictFromXml(filename, childindex=0, listing_names=[]):
	if not os.path.isfile(filename):
		raise IOError("Failed to open file "+filename+" for reading")
	dom = xml.dom.minidom.parse(filename)
	xmldict = nodeToDict(dom.childNodes[childindex],listing_names)
	return xmldict

### END BORROWED CODE

def dictToStr(xmldict, level=0):
	#setup line prefix -- tab level
	pre = ""
	for i in range(level):
		pre += "\t"
	if pre == "":
		pre = " "

	mystr = ""
	for k,v in list(xmldict.items()):
		#open dict key
		mystr += pre+"<"+str(k)+">"

		#insert values
		if type(v) == type({}):
			mystr += "\n"+pre+dictToStr(v, level=level+1)
		elif type(v) == type([]):
			mystr += listToStr(v, level=level+1)
		elif False and ' ' in v:
			mystr += '"'+str(v)+'"'
		else:
			mystr += str(v)

		#close dict key
		if mystr[-1:] == "\n":
			mystr += pre+"</"+str(k)+">\n"
		else:
			mystr += "</"+str(k)+">\n"
	return mystr

def listToStr(xmllist, level=0):
	#setup line prefix -- tab level
	pre = ""
	for i in range(level):
		pre += "\t"
	if pre == "":
		pre = " "

	mystr = ""
	for index,item in enumerate(xmllist):
		if type(item) == type([]):
			#list of lists
			#mystr += "\n"+pre+"<list><level>"+str(level)+"</level><index>"+str(index+1)+"</index><value>"
			mystr += "\n"+pre+"<list"+str(index)+">"
			mystr += listToStr(item, level=level+1)
			if mystr[-1:] == "\n":
				mystr += pre
			mystr += "</list"+str(index)+">"
			#mystr += "</value></list>"
		elif type(item) == type({}):
			#list of dicts
			#mystr += "\n"+pre+"<list><level>"+str(level)+"</level><index>"+str(index+1)+"</index><value>"
			mystr += "\n"+pre+"<list"+str(index)+">"
			mystr += dictToStr(item, level=level+1)
			if mystr[-1:] == "\n":
				mystr += pre
			mystr += "</list"+str(index)+">"
			#mystr += "</value></list>"
		else:
			mystr += str(item)+","

	#new line for item lists
	if mystr[-1:] == "\n":
		mystr += pre
	elif mystr[-1:] == ">":
		mystr += "\n"

	return mystr

def writeDictToXml(xmldict, filename, title=None):
	#compile XML
	mystr = dictToStr(xmldict)

	#insert title
	if title is not None:
		mystr = "<"+str(title)+">\n"+mystr+"</"+str(title)+">\n"
	else:
		mystr = "<apxml>\n"+mystr+"</apxml>\n"

	#write to file
	f = open(filename,"w")
	#f = sys.stderr
	f.write("<?xml version='1.0' encoding='us-ascii'?>\n")
	f.write(mystr)
	f.close()

	#check if it worked
	if os.path.isfile(filename):
		return True
	raise IOError("Failed to write XML data to file "+filename)

