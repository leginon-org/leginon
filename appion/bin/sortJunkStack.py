#!/usr/bin/env python

#python
import os
import re
import shutil
import subprocess
import sys
import time
#appion
import appionScript
import appiondata
import apDisplay
import apEMAN
import apStack
import apXmipp

class sortJunkStackScript(appionScript.AppionScript):
    #=====================
    def setupParserOptions(self):
        self.parser.set_usage("Usage: %prog --stack-id=ID [options]")
        self.parser.add_option("-s", "--stack-id", dest="stackid", type="int",
            help="Stack database id", metavar="ID")
        self.parser.add_option("--new-stack-name", dest="runname",
            help="New stack name", metavar="STR")

    #=====================
    def checkConflicts(self):
        if self.params['stackid'] is None:
            apDisplay.printError("stackid was not defined")
        if self.params['description'] is None:
            apDisplay.printError("substack description was not defined")
        if self.params['runname'] is None:
            apDisplay.printError("new stack name was not defined")


    #=====================
    def setRunDir(self):
        stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
        path = stackdata['path']['path']
        uppath = os.path.dirname(os.path.abspath(path))
        self.params['rundir'] = os.path.join(uppath, self.params['runname'])


    #=====================
    def start(self):
        # Path of the stack
        stackdata = apStack.getOnlyStackData(self.params['stackid'])
        fn_oldstack = os.path.join(stackdata['path']['path'], stackdata['name'])

        # Convert the stack to Xmipp
        apXmipp.breakupStackIntoSingleFiles(fn_oldstack)

        # Run sort junk
        cmd = "xmipp_sort_by_statistics -i partlist.doc"
        apDisplay.printColor(cmd, "cyan")
        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()

        # Create sorted stack
        apXmipp.gatherSingleFilesIntoStack("sort_junk.sel","sorted.hed")

        # Create average MRC
        apStack.averageStack("sorted.hed")

        # Remove intermediate stuff
        #os.unlink("partlist.doc")
        #shutil.rmtree("partfiles")

        # Upload results
        self.uploadResults()

        time.sleep(1)
        return

    #=====================
    def uploadResults(self):
        if self.params['commit'] is False:
            return

        # Get the new file order
        fh=open("sort_junk.sel",'r')
        lines=fh.readlines()
        i=0;
        fileorder={};
        for line in lines:
            args=line.split()
            if (len(args)>1):
                match=re.match('[A-Za-z]+([0-9]+)\.[A-Za-z]+',
                   (args[0].split('/'))[-1])
                if (match):
                    filenumber=int(match.groups()[0])
                    fileorder[i]=filenumber
                    i+=1
        fh.close()

        # Produce a new stack
        oldstack = apStack.getOnlyStackData(self.params['stackid'],msg=False)
        newstack = appiondata.ApStackData()
        newstack['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
        newstack['name'] = "sorted.hed"
        if newstack.query(results=1):
            apDisplay.printError("A stack with these parameters already exists")

        # Fill in data and submit
        newstack['oldstack'] = oldstack
        newstack['hidden'] = False
        newstack['substackname'] = self.params['runname']
        newstack['description'] = self.params['description']
        newstack['pixelsize'] = oldstack['pixelsize']
        newstack['junksorted'] = True
        newstack['project|projects|project'] = oldstack['project|projects|project']
        newstack.insert()

        # Insert stack images
        apDisplay.printMsg("Inserting stack particles")
        count=0
        total=len(fileorder.keys())
        if total==0:
            apDisplay.printError("No particles can be inserted in the sorted stack")
        for i in fileorder.keys():
            count += 1
            if count % 100 == 0:
                sys.stderr.write("\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b")
                sys.stderr.write(str(count)+" of "+(str(total))+" complete")

            # Get particle from the old stack
            oldparticle = apStack.getStackParticle(self.params['stackid'], fileorder[i]+1)

            # Insert particle
            newparticle = appiondata.ApStackParticlesData()
            newparticle['particleNumber'] = i+1
            newparticle['stack'] = newstack
            newparticle['stackRun'] = oldparticle['stackRun']
            newparticle['particle'] = oldparticle['particle']
            newparticle['mean'] = oldparticle['mean']
            newparticle['stdev'] = oldparticle['stdev']
            newparticle.insert()
        apDisplay.printMsg("\n"+str(total)+" particles have been inserted into the sorted stack")

        # Insert runs in stack
        apDisplay.printMsg("Inserting Runs in Stack")
        runsinstack = apStack.getRunsInStack(self.params['stackid'])
        for run in runsinstack:
            newrunsq = appiondata.ApRunsInStackData()
            newrunsq['stack'] = newstack
            newrunsq['stackRun'] = run['stackRun']
            newrunsq['project|projects|project'] = run['project|projects|project']
            newrunsq.insert()

        apDisplay.printMsg("finished")
        return

#=====================
if __name__ == "__main__":
    sortJunk = sortJunkStackScript()
    sortJunk.start()
    sortJunk.close()


