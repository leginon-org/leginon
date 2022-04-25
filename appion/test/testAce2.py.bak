#!/usr/bin/env python
import unittest
import subprocess
import os
import re
import glob
from urllib import urlretrieve

### This class is used to test the Ace2 program. It will dowload the needed test images from the AMI website, 
### then run ace2.exe and compare the results to what is ecpected. It will remove results files from a prior run
### when running subsequent tests. It does not remove the files after a test is run so the the usr can review 
### the result files if needed. Any functions in this class that begin with "test_" is a seperate test that
### will be executed by unittest.
 
### To run this test:
### 1. Create a temporary test directory and change directories to it. ex. mkdir ace2test, cd ace2test
### 2. run this file by providing the path to it. ex. python ../workspace/myami/appion/test/testAce2.py
### 3. review the results printed to the terminal.

class TestAce2(unittest.TestCase):

    def setUp(self):
        exename = 'ace2.exe'
        self.ace2exe = subprocess.Popen("which "+exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
        self.assertTrue(os.path.isfile(self.ace2exe), "Ace2.exe was not found")
        self.aceoutf = open("ace2.out", "a")
        self.aceerrf = open("ace2.err", "a")    
        self.defocus1 = None
        self.defocus2 = None
        self.angle_astigmatism = None
        self.amplitude_contrast = None
        self.confidence = None
        
    def tearDown(self):
        self.aceoutf.close()
        self.aceerrf.close()
                    
    def readLogFile(self,imagelog):
        # Read the log file to get final results for this image log file
        self.assertTrue( os.path.isfile(imagelog), "Ace2 did not run. Image Log file("+imagelog+") not found." )
        logf = open(imagelog, "r")
        for line in logf:
            sline = line.strip()
            if re.search("^Final Defocus \(m,m,deg\):", sline):
                parts = sline.split()
                self.defocus1 = float(parts[3])
                self.defocus2 = float(parts[4])
                self.angle_astigmatism = float(parts[5])
            elif re.search("^Amplitude Contrast:",sline):
                parts = sline.split()
                self.amplitude_contrast = float(parts[2])
            elif re.search("^Confidence:",sline):
                parts = sline.split()
                self.confidence = float(parts[1])
        logf.close()        

    def runAce2Test(self, imageUrl, defocus1, defocus2, angAstig, ampCont, conf, b='2', c='2.0', k='200.0', a='1.3656', e=['10.0','0.001'], r='0.0'):
        ### defocus1, defocus2, angAstig, ampCont, and conf are the expected output values that the test
        ### results will be compared to. b,c,k,a,e and r are ace2 input parameters.
        
        # Get the test image
        imgFile = imageUrl.split("/")[-1]
        # If the image is already there, don't bother downloading it again
        if not os.path.isfile(imgFile):
            urlretrieve(imageUrl, imgFile)
        self.assertTrue(os.path.isfile(imgFile), "Unable to download test image")
        
        # Remove any output files from a prior test run
        filelist = glob.glob(imgFile+".*")
        for f in filelist:
            os.remove(f)
        
        # Run Ace2 command
        commandline = ( self.ace2exe + " -i "+imgFile+" -b "+b+" -c "+c+" -k "+k+" -a "+a+" -e "+e[0]+","+e[1]+" -r "+r+"\n" )
        ace2proc = subprocess.Popen(commandline, shell=True, stderr=self.aceerrf, stdout=self.aceoutf)
        ace2proc.wait()
        
        # Compare results to what is expected
        imagelog = imgFile+".ctf.txt"
        self.readLogFile(imagelog)
        
        # We may want to modify these comparisons. Not sure if they give too much or too little wiggle room.
        self.assertAlmostEqual(self.defocus1, defocus1)
        self.assertAlmostEqual(self.defocus2, defocus2)
        self.assertTrue((angAstig - self.angle_astigmatism) < 2, "Angle of astigmatism is %f. Expected %f" % (self.angle_astigmatism, angAstig) )
        self.assertAlmostEqual(self.amplitude_contrast, ampCont, places=1)
        self.assertAlmostEqual(self.confidence, conf, places=1)        
    
    def test_ast_n_overfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1632/12oct01e_00059en.mrc"
        self.runAce2Test(imageUrl, defocus1=5.568862e-07,defocus2=6.559742e-07,angAstig=-70.235983,ampCont=0.091264,conf=0.815827)

    def test_ast_n_underfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1644/12oct01e_00055en.mrc"
        self.runAce2Test(imageUrl, defocus1=1.280421e-06 ,defocus2=1.318144e-06,angAstig=15.267624,ampCont=0.192086,conf=0.947226)

    def test_ast_a_overfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1635/12oct01e_00041ea.mrc"
        self.runAce2Test(imageUrl, defocus1=1.337478e-06 ,defocus2=1.482890e-06 ,angAstig=72.485569,ampCont=0.050000,conf=0.863265)

    def test_ast_a_underfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1633/12oct01e_00032ea.mrc"
        self.runAce2Test(imageUrl, defocus1=1.773057e-06 ,defocus2=1.867818e-06 ,angAstig=-66.550039,ampCont=0.182214,conf=0.957607)

    def test_ast_b_overfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1637/12oct01e_00050eb.mrc"
        self.runAce2Test(imageUrl, defocus1=1.477478e-06 ,defocus2=1.674565e-06 ,angAstig=-64.236799,ampCont=0.050000,conf=0.876410)

    def test_ast_b_underfocus(self):
        imageUrl = "http://ami.scripps.edu/redmine/attachments/1630/12oct01e_00054eb.mrc"
        self.runAce2Test(imageUrl, defocus1=1.533405e-06 ,defocus2=1.649353e-06 ,angAstig=29.912167,ampCont=0.194930,conf=0.958123)

if __name__ == '__main__':
    unittest.main()
        

