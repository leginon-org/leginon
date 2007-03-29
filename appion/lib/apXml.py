import cElementTree as ElementTree
import sys
import apDisplay

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
    >>> tree = ElementTree.parse('your_file.xml')
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

def updateXmlDict(dict):
	for param in dict.keys():
		if(dict[param].has_key('default') and dict[param]['default'] != None):
			#print param
			vtype = dict[param]['type']
			if vtype[:3].lower() == "int":
				dict[param]['default'] = int(dict[param]['default'])
				#print "  int=",int(dict[param]['default'])
			elif vtype.lower() == "float":
				dict[param]['default'] = float(dict[param]['default'])
				#print "  float=",float(dict[param]['default'])
			elif vtype[:4].lower() == "bool":
				dict[param]['default'] = str2bool(dict[param]['default'])
				#print "  bool=",str2bool(dict[param]['default'])
			else: # you are a string
				dict[param]['default']
				#print "  str= '"+dict[param]['default']+"'"
	return dict

def str2bool(string):
	if string[:1].lower() == 'f' or string[:1].lower() == 'n':
		return False
	else:
		return True

def printHelp(dict):
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


