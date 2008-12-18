import os
import sys
import time
import apDisplay
import subprocess

def executeImagicBatchFile(filename, verbose=False, logfile=None):
        """
        executes an IMAGIC batch file in a controlled fashion
        """
        waited = False
        t0 = time.time()
        try:
                if logfile is not None:
                        logf = open(logfile, 'a')
                        process = subprocess.Popen(filename, shell=True, stdout=logf, stderr=logf)
                elif verbose is False:
                        process = subprocess.Popen(filename, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                        process = subprocess.Popen(filename, shell=True)
                if verbose is True:
                        process.wait()
                else:
                        ### continuous check
                        waittime = 0.01
                        while process.poll() is None:
                                if waittime > 0.05:
                                        waited = True
                                        sys.stderr.write(".")
                                waittime *= 1.02
                                time.sleep(waittime)
        except:
                apDisplay.printWarning("could not run IMAGIC batchfile: "+filename)
                raise
        tdiff = time.time() - t0
        if tdiff > 20:
                apDisplay.printMsg("completed in "+apDisplay.timeString(tdiff))
        elif waited is True:
                print ""




