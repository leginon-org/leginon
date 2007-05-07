#!/usr/bin/python -O
# Python functions for selexon.py

#import particleData
import apDisplay
import apTemplate
import apImage
import apDatabase
import apParticle
import apUpload



def createDefaults():
	apDisplay.printWarning("this apParam/apUpload function should not be in use")

def printSelexonHelp():
	apDisplay.printWarning("this apXml function should not be in use")

def parseUploadInput(args,params):
	apDisplay.printError("this apUpload function no longer exists here")

def parsePrtlUploadInput(args,params):
	apDisplay.printError("this apUpload function no longer exists here")

def parseSelexonInput(args,params):
	apDisplay.printError("this apParam function is no longer in use")

def runFindEM(params,file):
	apDisplay.printError("this FindEM function no longer exists here")

def getOutDirs(params):
	apDisplay.printError("this apLoop function is no longer in use")

def createImageLinks(imagelist):
	apDisplay.printError("this ViewIt function no longer exists here")

def findPeaks(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def createJPG(params,img):
	apDisplay.printError("this ViewIt function no longer exists here")

def findCrud(params,file):
	apDisplay.printError("this ViewIt function no longer exists here")

def getImgSize(imgname):
	apDisplay.printWarning("this apDatabase function getImagesFromDB no longer exists here")
	return apDatabase.getImgSizeFromName(imgname)

def checkTemplates(params,upload=None):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	return apTemplate.checkTemplates(params, upload=upload)

def dwnsizeImg(params, imgdict):
	apDisplay.printWarning("this apFindEM function no longer exists here")
	apFindEM.processAndSaveImage(imgdict, params)
	return

def dwnsizeTemplate(params,filename):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.dwnsizeTemplate(filename, params)
	return

def binImg(img,binning):
	apDisplay.printWarning("this apImage function no longer exists here")
	return apImage.binImg(img,binning)

def filterImg(img,apix,res):
	apDisplay.printWarning("this apImage function no longer exists here")
	return apImage.filterImg(img,apix,res)

def pik2Box(params,file):
	apDisplay.printWarning("this apParticle function pik2Box no longer exists here")
	return apParticle.pik2Box(params,file)

def writeSelexLog(commandline, file=".selexonlog"):
	apDisplay.printError("this apParam function no longer exists here")

def getDoneDict(selexondonename):
	apDisplay.printError("this apLoop function no longer exists here")

def writeDoneDict(donedict,selexondonename):
	apDisplay.printError("this apLoop function no longer exists here")

def doneCheck(donedict,im):
	apDisplay.printError("this apLoop function no longer exists here")

def getImageData(imgname):
	apDisplay.printWarning("this apDatabase function getImageData no longer exists here")
	return apDatabase.getImageData(imgname)

def getPixelSize(imgdict):
	apDisplay.printWarning("this apDatabase function getPixelSize no longer exists here")
	return apDatabase.getPixelSize(imgdict)

def getImagesFromDB(session, preset):
	apDisplay.printWarning("this apDatabase function getImagesFromDB no longer exists here")
	return apDatabase.getImagesFromDB(session, preset)

def getAllImagesFromDB(session):
	apDisplay.printWarning("this apDatabase function getAllImagesFromDB no longer exists here")
	return apDatabase.getAllImagesFromDB(session)

def getDBTemplates(params):
	apDisplay.printWarning("this apDatabase function getDBTemplates no longer exists here")
	apDatabase.getDBTemplates(params)

def rescaleTemplates(img,params):
	#why is img passed? It is not used.
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.rescaleTemplates(params)
	return

def scaleandclip(fname,scalefactor,newfname):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.scaleAndClipTemplate(fname,scalefactor,newfname)
	return

def getDefocusPair(imagedata):
	apDisplay.printError("this DefocusPair function no longer exists here")

def getShift(imagedata1,imagedata2):
	apDisplay.printError("this DefocusPair function no longer exists here")

def findSubpixelPeak(image, npix=5, guess=None, limit=None, lpf=None):
	apDisplay.printError("this DefocusPair function no longer exists here")

def recordShift(params,img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertShift(img,sibling,peak):
	apDisplay.printError("this DefocusPair function no longer exists here")

def insertTemplateRun(params,runq,templatenum):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.insertTemplateRun(params,runq,templatenum)

def insertTemplateImage(params):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.insertTemplateImage(params)

def insertParticlePicks(params,imgdict,expid,manual=False):
	apDisplay.printWarning("this apParticle function insertParticlePicks no longer exists here")
	apParticle.insertParticlePicks(params,imgdict,expid,manual)

def insertManualParams(params,expid):
	apDisplay.printError("this apUpload function no longer exists here")

def insertSelexonParams(params,expid):
	apDisplay.printWarning("this apParticle function insertParticlePicks no longer exists here")
	apParticle.insertSelexonParams(params,expid)

def _checkTemplateParams(params,runq):
	apDisplay.printWarning("this apTemplate function no longer exists here")
	apTemplate.checkTemplateParams(params,runq)

def getProjectId(params):
	apDisplay.printError("this apUpload function no longer exists here")


