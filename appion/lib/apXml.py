import cElementTree
import sys
import apDisplay
import re

class XmlListConfig(list):
    def __init__(self, aList):
        for element in aList:
            if element:
                # treat like dict
                if len(element) == 1 or element[0].tag != element[1].tag:
                    self.append(XmlDictConfig(element))
                # treat like list
                elif element[0].tag == element[1].tag:
                    self.append(XmlListConfig(element))
            elif element.text:
                text = element.text.strip()
                if text:
                    self.append(text)


class XmlDictConfig(dict):
    """
    Example usage:
    >>> tree = cElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)
    And then use xmldict for what it is... a dict.
    """
    def __init__(self, parent_element):
        if parent_element.items():
            self.update(dict(parent_element.items()))
        for element in parent_element:
            if element:
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself 
                    aDict = {element[0].tag.lower(): XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if element.items():
                    aDict.update(dict(element.items()))
                self.update({element.tag.lower(): aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a 
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif element.items():
                self.update({element.tag.lower(): dict(element.items())})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag.lower(): element.text})

def readTwoXmlFiles(file1,file2):
	"""
	reads two XML files and creates a dictionary
	"""
	tree     = cElementTree.parse(file1)
	treeroot = tree.getroot()
	xmldict  = XmlDictConfig(treeroot)

	tree     = cElementTree.parse(file2)
	treeroot = tree.getroot()
	xmldict2 = XmlDictConfig(treeroot)

	xmldict = overWriteDict(xmldict,xmldict2)

	return updateXmlDict(xmldict)


def overWriteDict(dict1,dict2):
	"""
	merges dict2 into dict1 by inserting and overwriting values
	"""
	if len(dict2) > 0:
		for p in dict2:
			#if p in dict1:
				#print p,dict1[p],dict2[p]
				#dict1[p] = dict2[p]
			dict1[p] = dict2[p]
	return dict1

def generateParams(xmldict):
	"""
	generated the parameter dictionary based on the default values
	"""
	params = {}
	for p in xmldict:
		if 'default' in xmldict[p] and xmldict[p]['default'] != None:
			value = xmldict[p]['default']
			vtype = xmldict[p]['type']
			params[p] = _convertParamToType(value,vtype)
		else:
			params[p] = None
	return params

def checkParamDict(paramdict,xmldict):
	"""
	checks the parameter dictionary for type,limits, and conflict
	"""
	for p in paramdict:
		if 'type' in xmldict[p]:
			paramdict[p] = _convertParamToType(paramdict[p], xmldict[p]['type'])
		if 'limits' in xmldict[p]:
			minval,maxval = re.split(",",xmldict[p]['limits'])
			if paramdict[p] < float(minval):
				apDisplay.printError("parameter "+p+" is less than minimum allowed value: "+\
					str(paramdict[p])+"<"+str(minval))
			elif paramdict[p] > float(maxval):
				apDisplay.printError("parameter "+p+" is greater than maximum allowed value: "+\
					str(paramdict[p])+">"+str(maxval))
	return paramdict

def _convertParamToType(val,vtype):
	"""
	converts a value (val) into a type (vtype)
	"""
	if vtype[:3].lower() == "int":
		return int(val)
	elif vtype.lower() == "float":
		return float(val)
	elif vtype[:4].lower() == "bool":
		return str2bool(val)
	elif vtype[:3].lower() == "str" or vtype[:4].lower() == "path":
		return val
	else:
		apDisplay.printError("unknown type (type='"+vtype+"') in XML file")


def updateXmlDict(dict):
	"""
	converts all xml parameters into their desired type
	"""
	for param in dict.keys():
		if(dict[param].has_key('default') and dict[param]['default'] != None):
			dict[param]['default'] = _convertParamToType(dict[param]['default'],dict[param]['type'])
	return dict

def str2bool(string):
	"""
	converts a string into a bool
	""" 
	if string == True:
		return True
	if string == False or string[:1].lower() == 'f' or string[:1].lower() == 'n':
		return False
	else:
		return True

def printHelp(dict):
	"""
	print out help info for a function with XML file
	"""
	paramlist = dict.keys()
	paramlist.sort()
	maxlen = 0
	maxlentype = 0
	for param in paramlist:
		if len(param) > maxlen: 
			maxlen = len(param)
		if 'type' in dict[param] and len(dict[param]['type']) > maxlentype: 
			maxlentype = len(dict[param]['type'])
	for param in paramlist:
		if not 'alias' in dict[param] and \
			(not 'modify' in dict[param] or str2bool(dict[param]['modify']) == True):
			outstr = " "
			outstr += apDisplay.color(apDisplay.rightPadString(param,maxlen),"green")
			outstr += " :"

			if 'type' in dict[param] and dict[param]['type'] != None:
				outstr += " ("+apDisplay.rightPadString(dict[param]['type']+")",maxlentype+1)
				outstr += " :"
			if 'required' in dict[param] and str2bool(dict[param]['required']) == True:
				outstr += apDisplay.color(" REQUIRED","red")
			if 'description' in dict[param] and dict[param]['description'] != None:
				outstr += " "+dict[param]['description']
			elif dict[param].has_key('name') and dict[param]['name'] != None:
				outstr += dict[param]['name']
			if dict[param].has_key('default') and dict[param]['default'] != None:
				outstr += apDisplay.color(" (default: "+str(dict[param]['default'])+")","cyan")
			if dict[param].has_key('example') and dict[param]['example'] != None:
				outstr += " (example: "+str(dict[param]['example'])+")"

			print outstr
	sys.exit(1)


def fancyPrintDict(pdict):
	"""
	prints out two levels of a dictionary
	"""
	pkeys = pdict.keys()
	pkeys.sort()
	maxlen = 0
	print "----------"
	for p in pkeys:
		if len(p) > maxlen: maxlen = len(p)
	for p in pkeys:
		print " ",apDisplay.rightPadString(p+":",maxlen+2),\
			apDisplay.colorType(pdict[p])
	print "----------"

