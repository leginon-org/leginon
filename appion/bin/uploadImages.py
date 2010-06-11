#!/usr/bin/env python

"""
This is a template on how to construct a new Appion Script from scratch

At the top you have the '#!/usr/bin/env python'

this tells the computer that this is a python program and it tells it
to run the env program in the /usr/bin directory to find the location
of the python interpreter
"""

import os
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apModel

"""
Next, you have the import commands

You may not know which module you will need, so start with a couple
and add more as you need them. For an Appion Script you will at least
need the 'appionScript' module (or file) and the 'os' module is also
very handy. 'apDisplay' is used to print messages, wanrings and errors.
apStack will be used to get information about a stack.

For Appion libraries we use the system 'from appionlib import X'. This
tells python to go into the appionlib directory and read the file 'X.py'.
"""

"""
Now we need to create a class for our program that will inherit all the
properties of appionScript.

In this case I gave my program the name 'ExampleScript' and then put
appionScript.AppionScript in parentheses. The latter part tells python
that my new class called ExampleScript will inherit all properties from
AppionScript located in the appionScript module (or file). The
appionScript.AppionScript is required for an Appion Script.

Within a new Appion Script class there are four required functions:
setupParserOptions(), checkConflicts(), setRunDir(), and start(). Beyond
this you can create any new function that you would like and there are two
other special functions that you can override, OnInit() and OnClose(). These
function are described in more detail below.

Typically, I like to keep setupParserOptions(), checkConflicts(), setRunDir()
at the top of the class and start() as the last function in the class. This
makes it easy to find them when reading another person's code.
"""

#=====================
#=====================
class ExampleScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		This function is used to define any command line arguments.
		Things like stackid, modelid, templateid, or shuffle files.

		As part of Appion Script, several global variables are already defined:
		runname, description, projectid, rundir, and commit. Of these only
		runname is required

		The commandline is parsed using the OptParse library in python,
		see http://docs.python.org/library/optparse.html for documentation.

		There are three major types of options: (1) strings, floats, and ints,
		(2) true/false, and (3) choosing from a list.

		The first type of option is obtaining a string, float, or int from the user.
		It has the following format:
		"""
		self.parser.add_option("--username", dest="username",
			help="Your user name", metavar="NAME")
		self.parser.add_option("--file", dest="filename",
			help="Some file", metavar="FILE")
		self.parser.add_option("-s", "--id", "--stackid", dest="stackid", type="int",
			help="A stack id ", metavar="#")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="An initial model id ", metavar="#")
		self.parser.add_option("--p", "--pi", dest="pi", type="float", default=3.1415926,
			help="The value of pi", metavar="#")
		"""
		When defining a new commandline option, the first to do is define how you will
		set this option. Valid options are a single hyphen and a single letter or two
		hyphens and any number of letter. You can alos specify as many different ways
		to set you option as you want. The next flag is the destination or 'dest', this
		defines what your value will be call in self.params. For example, the username
		will be stored in self.params['username'].

		Next,note that the flag 'type' is used to define the type, by default it is string.
		So, this is left out in the first case. In the third option, the flag
		'default' is used to set a default value, is general the default is the python
		reserved value of 'None'. The flags 'help' and 'metavar' are used when printing
		the help message to the command line.

		The second type of option is true/false:
		"""
		self.parser.add_option("-D", "--do-it", dest="doit", default=True,
			action="store_true", help="Do it")
		self.parser.add_option("--do-not-do-it", dest="doit", default=True,
			action="store_false", help="Do not do it")
		"""
		In this case we have two options going to the same dest, one sets the
		value to true the other to false through the 'action' flag. In this
		case, by default the value is True. Note 'metavar' is not defined.

		The third type of option is a choice:
		"""
		self.fruittypes = ('orange', 'apple', 'banana')
		self.parser.add_option("--fruit", dest="fruit", default="orange",
			type="choice", choices=self.fruittypes,
			help="Favorite type of fruit", metavar="..")
		"""
		Here you provide a list of acceptable option for the user to choose from
		"""

	#=====================
	def checkConflicts(self):
		"""
		After you have set the options you want to have, you need to check to make sure
		they are valid and if they are required.

		For this script, we'll say that the stackid is required
		"""
		if self.params['stackid'] is None:
			apDisplay.printError("Please provide a user id, e.g. --stackid=15")
		"""
		Here we check is the stackid is not defined, i.e., it is equal to 'None'
		If it is None the program will print an Error and automatically exit

		Next, I want to check the username does not contain a space
		"""
		if self.params['username'] is not None and ' ' in self.params['username']:
			apDisplay.printError("User names cannot contains spaces, '%s'"
				%(self.params['username']))
		"""
		If there is a space it exit the program

		Next we can look up the user id to make sure it is valid
		"""
		if not self.isStackId(self.params['stackid']):
			apDisplay.printError("Invaid user id")
		apDisplay.printMsg("User id is valid")
		"""
		We print a general message, if the stackid is valid

		Next we can look up the see if a file exists
		"""
		if self.params['filename'] is not None and not os.path.isfile(self.params['filename']):
			apDisplay.printWarning("File does not exist")
		"""
		In this case, the program does not exit, it just prints a warning and continues on
		"""

	#=====================
	def isStackId(self, stackid):
		"""
		Arbitrary requirements for a stackid
		"""
		if stackid < 1:
			return False
		elif stackid > 99999:
			return False
		return True

	#=====================
	def setRunDir(self):
		"""
		This function is only run, if --rundir is not defined on the commandline

		This function decides when the results will be stored. You can do some complicated
		things to set a directory.

		Here I will use information about the stack to set the directory
		"""
		### get the path to input stack
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackpath = os.path.abspath(stackdata['path']['path'])
		### go down two directories
		uponepath = os.path.join(stackpath, "..")
		uptwopath = os.path.join(uponepath, "..")
		### add path strings; always add runname to end!!!
		rundir = os.path.join(uptwopath, "example", self.params['runname'])
		### same thing in one step
		rundir = os.path.join(stackpath, "../../example", self.params['runname'])
		### good idea to set absolute path,
		### cleans up 'path/stack/stack1/../../example/ex1' -> 'path/example/ex1'
		self.params['rundir'] = os.path.abspath(rundir)
		"""
		In all cases, we set the value for self.params['rundir']
		"""

	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def start(self):
		"""
		This is the core of your function.
		You decide what happens here!
		"""
		apDisplay.printMsg("\n\n")
		### get info about the stack
		apDisplay.printMsg("Information about stack id %d"%(self.params['stackid']))
		apDisplay.printMsg("\tboxsize %d pixels"%(apStack.getStackBoxsize(self.params['stackid'], msg=False)))
		apDisplay.printMsg("\tpixelsize %.3f Angstroms"%(apStack.getStackPixelSizeFromStackId(self.params['stackid'], msg=False)))
		apDisplay.printMsg("\tsize %d particles"%(apStack.getNumberStackParticlesFromId(self.params['stackid'], msg=False)))

		### get info about the model
		if self.params['modelid'] is not None:
			apDisplay.printMsg("Information about model id %d"%(self.params['modelid']))
			modeldata = apModel.getModelFromId(self.params['modelid'])
			apDisplay.printMsg("\tboxsize %d pixels"%(modeldata['boxsize']))
			apDisplay.printMsg("\tpixelsize %.3f Angstroms"%(modeldata['pixelsize']))
		apDisplay.printMsg("\n\n")

"""
Last we need to tell python how to run your function

The line "if __name__ == '__main__':" makes sure that the function
will only run from the commandline, if someone were to import
this file nothing would happen.

The first line creates an instance of the class defined above.
This reads the commandline, runs checkConflicts, and set the rundir.
Next the start function is run that does all the stuff you defined. And
finally the function is closed.
"""


#=====================
#=====================
if __name__ == '__main__':
	examplescript = ExampleScript()
	examplescript.start()
	examplescript.close()

