#!/usr/bin/env python

'''
Automated Common Lines: A method for iteratively creating ab 
initio 3d models from a stack of class averages. The algorithm inputs 
a weighted and randomly generated sequence of class averages into angular 
reconstitution N times to create N different 3D models. 
It then uses a combination of maximum-likelihood 3D alignment and 3D 
multivariate statistical analysis to sort through the resulting 3D models. 
The last step is 3D clustering utilizing the affinity propagation algorithm,
which parses through the output and classifies the models without relying
on a specified number of clusters. The final 3D clusters are summed & scored 
based on multiple different scoring criteria. 
'''

# python
import glob
import os
import shutil
import subprocess
import textwrap

# Appion
from appionlib import appiondata
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apIMAGIC
from appionlib import apParam
from appionlib import apThread
from appionlib import apXmipp
from appionlib import apCommonLines
from appionlib import apChimera

class helpDialogs:

	def classavgs(self):
		h = "full path to the class averages used for iterative model creation"
		return h	
		
	def templatestackid(self):
		h = "ID of template stack used for iterative model creation"
		return h

	def clusterid(self):
		h = "ID of clustering stack used for iterative model creation"
		return h 
	
	def refine_templatestackid(self):
		h = "ID of template stack used for refinement"
		return h

	def refine_clusterid(self):
		h = "ID of clustering stack used for refinement"
		return h	
	
	def refine_classavgs(self):
		h = "The aligned and summed models are iteratively refined against an input "
		h+= "stack of class averages. It is possible to specify distinct stacks for "
		h+= "the model building portion and the refinement portion. If you would like "
		h+= "to use a different set of class averages for the refinement, specify "
		h+= "the full path here. If nothing is specified, the same classes will be "
		h+= "used for all portions of the procedure."
		return h
	
	def prealign(self):
		h = "iteratively align the class averages "
		h+= "to each other prior to carrying out iterative angular reconstitution. "
		h+= "This option has been very helpful in cases when the class averages may "
		h+= "not be perfectly translationally aligned, which would produce poor "
		h+= "results when input into angular reconstitution."
		return h
	
	def scale(self):
		h = "scale the class averages to a boxsize of 64x64 prior to iterative model "
		h+= "creation"
		return h	
		
	def apix(self):
		h = "pixel size of class averages used for initial model construction"
		return h	

	def refineapix(self):
		h = "pixel size of class averages used for refinement. (optional)"
		return h

	def threes(self):
		h = "Only reconstruct groups of 3 images calculated in angular reconstitution. "
		h+= "Rather than using ALL of the class averages for the raw volume "
		h+= "calculations, if this option is specified, all raw volumes will consist "
		h+= "of a group of 3 images. This dramatically speeds up initial volume "
		h+= "calculation. The volumes will still be aligned and refined as usual. "
		return h	
		
	def non_weighted_sequence(self):
		h = "if this is specified, then the "
		h+= "sequence of addition into angular reconstitution will "
		h+= "be completely randomized, rather than weighted and randomized."
		return h	
		
	def asqfilt(self):
		h = "ASQ filtering means Amplitude-Square-Root and "
		h+= "is described in papers, like: Marin van Heel, Michael Schatz, and Elena "
		h+= "Orlova, 'Correlation Functions Revisited', Ultramicroscopy 46 (1992) "
		h+= "304-316. This filtering is important if one does not want the sinogram "
		h+= "(and a sine-correlation-function derived from it) to be largely dominated "
		h+= "by low-frequency information. The ASQ filter functions largely as a "
		h+= "high-pass filter (see paper)."
		return h	
		
	def linear_mask(self):
		h = "Radius of the linear mask (in Angstroms) to be imposed on the sinogram "
		h+= "and within which the statistics will be calculated for the normalization "
		h+= "of the sinograms. For best results, this value should be exactly 1/2 * "
		h+= "the diameter of your particle. For example, for a particle of diameter "
		h+= "200 Angstroms, this value should be 100. Default is ((box-2)/2)*apix, so "
		h+= "For NO masking answer '0'"
		return h	
		
	def first_image(self):
		h = "specify the first image (numbering starts with 0) to "
		h+= "be used during C1 startup, rather than randomizing"
		return h	
		
#	def symmetry(self):
#		h = "symmetry of the object. This is automatically defaulted to the "
#		h+= "suggested C1 symmetry"
#		return h	
		
	def num_volumes(self):
		h = "number of volumes to create using angular reconstitution"
		return h	
		
	def ang_inc(self):
		h = "angular increment for Euler search within the sinogram"
		return h	
		
	def keep_ordered(self):
		h = "percentage of the best class averages to keep for the "
		h+= "actual 3D reconstruction. This value is determined by the error in "
		h+= "angular reconstitution for each input class average"
		return h	
		
	def mask_radius(self):
		h = "Radius of the mask for the refinement of the initial volume "
		h+= "calculated by angular reconstitution (Angstroms). For best results, "
		h+= "this value should be slightly larger than the diameter of your particle "
		h+= "(e.g. for a 200 Angstrom particle, this value can be ~240/2 ~= 120 "
		h+= "Angstroms). The default value is 'linear_mask' parameter * 1.2."
		return h	
		
	def inner_radius(self):
		h = "inner radius for the alignment search of volume refinement (Angstroms) "
		h+= "Default is 0."
		return h	
		
	def outer_radius(self):
		h = "outer radius for the alignment search during volume refinement "
		h+= "(Angstroms). The default value is 'mask_radius'*0.8"
		return h	
		
	def ham_win(self):
		h = "similar to lp-filtering parameter, smooths out the filter used in "
		h+= "3d reconstruction"
		return h	

	def useEMAN1(self):
		h = "use EMAN1 for the common lines generation (cross-common lines) instead "
		h+= "of angular reconstitution. "
		return h	
		
	def images_per_volume(self):
		h = "If using EMAN1 only, this parameter refers to the number of images to use "
		h+= "for constructing each 3D map. The input averages correspond to the total 'pool' "
		h+= "from which a subset will be selected for analysis by cross-common lines. N "
		h+= "different subsets will be randomly calculated and selected, where N refers "
		h+= "to the total number of maps prior to 3D classification & refinement."
		return h		
		
	def lp(self):
		h = "low-pass filter the reconstructed 3-D model to specified resolution "
		h+= "(Angstroms) prior to masking"
		return h	
		
	def nref(self):
		h = "number of 3D references to generate for Xmipp maximum-likelihood alignment"
		return h	
		
	def num_eigens(self):
		h = "number of 3D Eigenvectors (Eigenvolumes) to create during Principal "
		h+= "Component Analysis for data reduction"
		return h	
		
	def PCA(self):
		h = "don't use Principal Component Analysis to reduce the dimensionality of "
		h+= "the resulting 3D volumes prior to clustering."
		return h	
		
	def recalculate(self):
		h = "optional parameter: specify only if you wish to recalculate the 3D "
		h+= "volumes after PCA data reduction. Does NOT affect any results, and is "
		h+= "only present for visualization purposes of the effects of PCA"
		return h	
		
	def preftype(self):
		h = "preference value for affinity propation which influences the resulting "
		h+= "number of 3D class averages. choose from 'median', 'minimum', or "
		h+= "'minlessrange'. 'median' will result in the greatest amount of classes, "
		h+= "followed by 'minimum', while 'minlessrange' results in the fewest"
		return h	
		
	def presumed_sym(self):
		h = "presumed symmetry of the particles. This is ONLY used in the calculation "
		h+= "of Euler jumpers during the evaluation of the final model and does not "
		h+= "affect the volumes in any way. It's defaulted to c1, but if your "
		h+= "particles have high symmetry, then the Euler jumper angles will come "
		h+= "out higher than what they should be and may affect the selection of "
		h+= "optimal models."
		return h	
		
	def do_not_remove(self):
		h = "specify if you want to keep miscellaneous files associated with "
		h+= "angular reconstitution (e.g. sinograms) NOTE: keeping these files "
		h+= "takes up huge amounts of diskspace"
		return h	
		
	def mem(self):
		h = "only for the storage of the references, which is usually not "
		h+= "necessary to modify for small stacks"
		return h	
		
#	def nproc(self):
#		h = "total number of processors to use (common lines and refinement)"
#		return h	
		
	def start_at(self):
		h = "Specify "
		h+= "this option if you want to pick up the program where it last left off. "
		h+= "Valid options are: '3D_align', '3D_refine', '3D_assess'. "
		h+= "'3D_align' will start at the "
		h+= "alignment step, and assumes existence of the volumes directory. "
		h+= "'3D_refine' will start at the refinement and assumes that alignment "
		h+= "parameters exist. Note that the volumes MUST be aligned."
		h+= " '3D_assess' skips everything, and just "
		h+= "does the final volume assessment."
		return h
																																																																	
	
class OptiMod(appionScript.AppionScript):

	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --classavgs=<name> --num_volumes=<num> "
			+"--apix=<pixel> [options]")		

		wrapper = textwrap.TextWrapper(width=80)	
		hd = helpDialogs()
		self.parser.set_defaults(nproc=1)
			
		### basic params
		self.parser.add_option("--classavgs", dest="classavgs",
			help=wrapper.fill(hd.classavgs()), metavar="PATH")
		self.parser.add_option("--templatestackid", dest="templatestackid",
			help=wrapper.fill(hd.templatestackid()), metavar="int")
		self.parser.add_option("--clusterid", dest="clusterid",
			help=wrapper.fill(hd.clusterid()), metavar="int")			
		self.parser.add_option("--apix", dest="apix", type="float",
			help=wrapper.fill(hd.apix()), metavar="INT")
			
		### pre-processing of class averages
		self.parser.add_option("--prealign", dest="prealign", default=False, 
			action="store_true", help=wrapper.fill(hd.prealign()), metavar="BOOL")
		self.parser.add_option("--scale", dest="scale", default=False, 
			action="store_true", help=wrapper.fill(hd.scale()), metavar="BOOL")
			
		### Angular Reconstitution
		self.parser.add_option("--threes", dest="threes", default=False, 
			action="store_true", help=wrapper.fill(hd.threes()), metavar="BOOL")
		self.parser.add_option("--non_weighted_sequence", dest="non_weighted_sequence", 
			default=False, action="store_true", 
			help=wrapper.fill(hd.non_weighted_sequence()), metavar="BOOL")
		self.parser.add_option("--asqfilter", dest="asqfilt", default=False, 
			action="store_true", help=wrapper.fill(hd.asqfilt()), metavar="BOOL")		
		self.parser.add_option("--linear_mask", dest="linmask", type="float", default=0,
			help=wrapper.fill(hd.linear_mask()), metavar="<(box-2)/2*apix>")
		self.parser.add_option("--first_image", dest="firstimage", type="int", 
			default=None, help=wrapper.fill(hd.first_image()), metavar="INT")
#		self.parser.add_option("--symmetry", dest="sym", type="str", default="C1",
#			help=wrapper.fill(hd.symmetry()), metavar="<C1>")
		self.parser.add_option("--num_volumes", dest="num_volumes", type="int",
			help=wrapper.fill(hd.num_volumes()), metavar="INT")
		self.parser.add_option("--ang_inc", dest="ang_inc", type="int", default=2,
			help=wrapper.fill(hd.ang_inc()), metavar="<2>")
		self.parser.add_option("--keep_ordered", dest="keep_ordered", type="int", 
			default=90, help=wrapper.fill(hd.keep_ordered()), metavar="<90>")

		### EMAN1 cross-common lines
		self.parser.add_option("--useEMAN1", dest="useEMAN1", default=False, 
			action="store_true", help=wrapper.fill(hd.useEMAN1()), metavar="BOOL")	
		self.parser.add_option("--images_per_volume", dest="images_per_volume", type="int",
			help=wrapper.fill(hd.images_per_volume()), metavar="INT")
			
		### 3D refinement
		self.parser.add_option("--refine_templatestackid", dest="r_templatestackid",
			help=wrapper.fill(hd.refine_templatestackid()), metavar="int")
		self.parser.add_option("--refine_clusterid", dest="r_clusterid",
			help=wrapper.fill(hd.refine_clusterid()), metavar="int")		
		self.parser.add_option("--refine_classavgs", dest="refine_classavgs",
			help=wrapper.fill(hd.refine_classavgs()), metavar="PATH")
		self.parser.add_option("--refine_apix", dest="refineapix", type="float",
			help=wrapper.fill(hd.refineapix()), metavar="INT")		
		self.parser.add_option("--mask_radius", dest="mask_radius", type="int",
			help=wrapper.fill(hd.mask_radius()), metavar="<linear_mask*1.2>")
		self.parser.add_option("--inner_radius", dest="inner_radius", type="int", 
			default=0, help=wrapper.fill(hd.inner_radius()), metavar="<0>")
		self.parser.add_option("--outer_radius", dest="outer_radius", type="int",
			help=wrapper.fill(hd.outer_radius()), metavar="<linear_mask*0.8>")		
	
		### 3D reconstruction
		self.parser.add_option("--ham_win", dest="ham_win", type="float", default=0.8,
			help=wrapper.fill(hd.ham_win()), metavar="<0.8>")
		self.parser.add_option("--3d_lpfilt", dest="3d_lpfilt", type="int", default=30,
			help=wrapper.fill(hd.lp()), metavar="<30>")
			
		### Xmipp maximum-likelihood alignment
		self.parser.add_option("--nref", dest="nref", type="int", default=1,
			help=wrapper.fill(hd.nref()), metavar="<1>")	
			
		### Principal Component Analysis (Multivariate Statistical Analysis)
		self.parser.add_option("--numeigens", dest="numeigens", type="int", default=20,
			help=wrapper.fill(hd.num_eigens()), metavar="<20>")
		self.parser.add_option("--no-PCA", dest="PCA", default=True, action="store_false",
			help=wrapper.fill(hd.PCA()), metavar="BOOL")
		self.parser.add_option("--recalculate_volumes", dest="recalculate", 
			default=False, action="store_true", help=wrapper.fill(hd.recalculate()), 
			metavar="BOOL")
				
		### Affinity propagation clustering
		self.parser.add_option("--preftype", dest="preftype", type="str", 
			default="median", help=wrapper.fill(hd.preftype()), metavar="STR")

		### Final model evaluation
		self.parser.add_option("--presumed_sym", dest="presumed_sym", type="str", 
			default="C1", help=wrapper.fill(hd.presumed_sym()), metavar="<C1>")
		
		### Miscellaneous
		startchoices = ("none","3D_align","3D_refine","3D_assess")
		self.parser.add_option("--start_at", dest="start_at", type="choice", 
			choices=startchoices, default="none", help=wrapper.fill(hd.start_at()),
			metavar="CHOICE")
		self.parser.add_option("--do_not_remove", dest="do_not_remove", default=False, 
			action="store_true", help=wrapper.fill(hd.do_not_remove()), metavar="BOOL")
		self.parser.add_option("--memory", dest="memory", default='2gb',
			help=wrapper.fill(hd.mem()), metavar="<2gb>")
		self.parser.add_option("--mass", dest="mass", type="int", 
			help="mass of particle (in kDa). this is ONLY necessary for the chimera snapshots", metavar="INT")			
#		self.parser.add_option("--nproc", dest="nproc", type="int", 
#			default=1, help=wrapper.fill(hd.nproc()), metavar="<1>")	
							
		return		
	
	def checkConflicts(self):
		""" basic error handlign for running scripts """
	
		### check for IMAGIC installation
		try:
			self.imagicroot = apIMAGIC.checkImagicExecutablePath()
		except:
			c = "some IMAGIC functions, e.g. prealignment and angular reconstitution "
			c+= "may not work. Use EMAN instead"
			apDisplay.printWarning(c)
			self.imagicroot = None
			self.params['useEMAN1'] is True

		### check class averages
		if self.params['templatestackid'] is not None:
			self.stackdata = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
			self.clsname = self.stackdata['templatename']
			self.params['apix'] = self.stackdata['apix']
			self.params['boxsize'] = self.stackdata['boxsize']
			self.params['oldavgs'] = os.path.join(self.stackdata['path']['path'], self.clsname[:-4]+".hed")
			self.params['avgs'] = os.path.basename(self.clsname)
		elif self.params['clusterid'] is not None:
			self.stackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
			self.clsname = self.stackdata['avg_imagicfile']
			self.params['apix'] = self.stackdata['clusterrun']['pixelsize']
			self.params['boxsize'] = self.stackdata['clusterrun']['boxsize']
			self.params['oldavgs'] = os.path.join(self.stackdata['path']['path'], self.clsname[:-4]+".hed")
			self.params['avgs'] = self.clsname
		elif self.params['classavgs'] is not None:
			if self.params['apix'] is None:
				apDisplay.printError("enter pixel size for manually uploaded classes")
			self.params['oldavgs'] = self.params['classavgs']
			bavgs = os.path.basename(self.params['classavgs'])
			self.params['avgs'] = bavgs
		else:
			apDisplay.printError("enter class averages for the run")

		if not os.path.isfile(os.path.abspath(self.params['oldavgs'])):
			apDisplay.printError("cannot find input class averages")			
			
		if self.params['templatestackid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("enter either templatestack ID OR cluster ID")
		if self.params['templatestackid'] is not None and self.params['classavgs'] is not None:
			apDisplay.printError("enter either templatestack ID OR manually uploaded classes")
		if self.params['clusterid'] is not None and self.params['classavgs'] is not None:
			apDisplay.printError("enter either cluster ID OR manually uploaded classes")			
		
		### pretreatment
		if self.imagicroot is not None and self.params['prealign'] is True:
			warning = "particles will not be prealigned, IMAGIC is not installed or path "
			warning+= "to IMAGIC cannot be located"
			apDisplay.printWarning(warning)	
		
		### basic input parameters
		self.params['numpart'] = apFile.numImagesInStack(self.params['oldavgs'])
		if self.params['numpart'] < 3:
			apDisplay.printError("need at least 3 class averages in stack to run")			
		self.params['boxsize'] = apFile.getBoxSize(self.params['oldavgs'])[0]
		if self.params['num_volumes'] is None:
			apDisplay.printError("specify the number of volumes to produce")
		if self.params['apix'] is None:
			apDisplay.printError("enter pixel size of class averages")					

		### refinement class averages
		if self.params['r_templatestackid'] is not None:
			self.rstackdata = appiondata.ApTemplateStackData.direct_query(self.params['r_templatestackid'])
			self.rclsname = self.rstackdata['templatename']
			self.params['refineapix'] = self.rstackdata['apix']
			self.params['refineboxsize'] = self.rstackdata['boxsize']
			self.params['oldravgs'] = os.path.join(self.rstackdata['path']['path'], self.rclsname[:-4]+".hed")
			self.params['ravgs'] = os.path.basename(self.rclsname)
		elif self.params['r_clusterid'] is not None:
			self.rstackdata = appiondata.ApClusteringStackData.direct_query(self.params['r_clusterid'])
			self.rclsname = self.rstackdata['avg_imagicfile']
			self.params['refineapix'] = self.rstackdata['clusterrun']['pixelsize']
			self.params['refineboxsize'] = self.rstackdata['clusterrun']['boxsize']
			self.params['oldravgs'] = os.path.join(self.rstackdata['path']['path'], self.rclsname[:-4]+".hed")
			self.params['ravgs'] = self.rclsname
		elif self.params['refine_classavgs'] is not None:
			rbavgs = os.path.basename(self.params['refine_classavgs'])
			self.params['ravgs'] = rbavgs
			self.params['refineboxsize'] = apFile.getBoxSize(self.params['oldravgs'])[0]
			if self.params['refineapix'] is None:
				warning = "refinement pixel size not specified ... assuming it is the same"
				apDisplay.printWarning(warning)
				self.params['refineapix'] = self.params['apix']		
		else:
#			self.params['ravgs'] = None
			self.params['oldravgs'] = self.params['avgs']
 			self.params['ravgs'] = self.params['avgs']
			self.params['refineapix'] = self.params['apix']
			self.params['refineboxsize'] = self.params['boxsize']
			
		if not os.path.isfile(os.path.abspath(self.params['oldravgs'])):
			warning = "cannot find class averages for refinement using the "
			warning+= "specified path. Original averages will be used instead."
			apDisplay.printWarning(warning)
			self.params['oldravgs'] = self.params['avgs']
			self.params['ravgs'] = self.params['avgs']
					
		### check for scaling		
		if self.params['scale'] is True:
			self.scalefactor = float(64.0 / self.params['boxsize'])
			self.params['apix'] = self.params['apix'] / self.scalefactor
			self.params['boxsize'] = 64	
		else:
			self.scalefactor = 1
			
		### angular reconstitution checks
		if self.params['keep_ordered'] < 1.0: ### probably specified as a fraction
			self.params['keep_ordered'] = self.params['keep_ordered'] * 100	### convert to percentage
		self.params['keep_ordered_num'] = self.params['numpart'] * self.params['keep_ordered'] / 100

		### EMAN1 cross common lines checks
		if self.params['useEMAN1'] is True:
			if self.params['images_per_volume'] is None:
				self.params['images_per_volume'] = int(self.params['numpart'] * 0.66)
			if self.params['images_per_volume'] > self.params['numpart']:
				warning = "number of images per volume greater than number of class averages "
				warning+= "in input. Setting to (0.66)*(num_averages)"
				apDisplay.printWarning(warning)
				self.params['images_per_volume'] = int(self.params['numpart'] * 0.66)
			if self.params['images_per_volume'] > self.params['numpart'] * 0.75:
				warning = "consider asking for less images per volume to provide more variety "
				warning = "during common lines search"
				apDisplay.printWarning(warning)
			
		### number of processors for threading ONLY works on a single node
		self.params['threadnproc'] = apParam.getNumProcessors()
			
		### refinement parameters
		if self.params['linmask'] == 0:
			self.params['linmask'] = (self.params['boxsize']-2)/2*self.params['apix']
		if self.params['mask_radius'] is None and self.params['linmask'] != 0:
			self.params['mask_radius'] = self.params['linmask'] * 1.2
		elif self.params['mask_radius'] is None and self.params['linmask'] == 0:
			self.params['mask_radius'] = self.params['boxsize'] * self.params['refineapix']
		if self.params['outer_radius'] is None:
			self.params['outer_radius'] = self.params['mask_radius'] * 0.8

		return	

	'''
	def setRunDir(self):

		if self.params['templatestackid'] is not None:
			stackdata = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
		elif self.params['clusterid'] is not None:
			stackdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		else:
			apDisplay.printError("class averages not in the database")
			
		path = os.path.abspath(os.path.join(stackdata['path']['path'], "../..", "common_lines"))
		self.params['rundir'] = os.path.join(path, self.params['runname'])
		
		return
	'''

	def upload(self):
		''' insert into database, if commit is checked '''
		
		### path object
		pathq = appiondata.ApPathData()
		pathq['path'] = self.params['rundir']

		### acl run object
		aclq = appiondata.ApAutomatedCommonLinesRunData()
		aclq['path'] = pathq
		aclq['runname'] = self.params['runname']
		### check unique run
#		uniquerun = aclq.query(results=1)
#		if uniquerun:
#			apDisplay.printError("runname already exists in the database")
		
		### acl params object
		aclparamq = appiondata.ApAutomatedCommonLinesParamsData()
		aclparamq['num_averages'] = self.params['numpart']
		aclparamq['num_volumes'] = self.params['num_volumes']
#		aclparamq['symmetry'] = appiondata.ApSymmetryData.direct_query(self.params['symid'])
		aclparamq['num_alignment_refs'] = self.params['nref']
		aclparamq['angular_increment'] = self.params['ang_inc']
		aclparamq['keep_ordered'] = self.params['keep_ordered']
		aclparamq['threed_lpfilt'] = self.params['3d_lpfilt']
		aclparamq['hamming_window'] = self.params['ham_win']
		aclparamq['non_weighted_sequence'] = self.params['non_weighted_sequence']
		aclparamq['PCA'] = self.params['PCA']
		aclparamq['numeigens'] = self.params['numeigens']
		aclparamq['prealign_avgs'] = self.params['prealign']
		aclparamq['scale'] = self.params['scale']
		aclparamq['recalculate_volumes'] = self.params['recalculate']
		aclparamq['preference_type'] = self.params['preftype']
#		aclparamq['do_not_remove'] = self.params['do_not_remove']

		### finish acl run object	
		aclq['acl_params'] = aclparamq
		aclq['pixelsize'] = self.params['apix']
		aclq['boxsize'] = self.params['boxsize']
		if self.params['templatestackid'] is not None:
			aclq['templatestackid'] = appiondata.ApTemplateStackData.direct_query(self.params['templatestackid'])
		else:
			aclq['clusterid'] = appiondata.ApClusteringStackData.direct_query(self.params['clusterid'])
		aclq['description'] = self.params['description']
		aclq['REF|projectdata|projects|project'] = self.params['projectid']
		aclq['hidden'] = False
		
		if self.params['commit'] is True:
			aclq.insert()
		else:
			apDisplay.printWarning("NOT commiting results to database")
			
		return
	
	############################################################################ 
	###                                                                      ###
	###                         MAIN ALGORITHM                               ###
	###                                                                      ###
	############################################################################	
	

	def start(self):
		''' 
		OptiMod script 
		'''
		
		###############     define short-hand parameter names       ############
			
		refine = True
		rundir = self.params['rundir']
		box = self.params['boxsize']
		rbox = self.params['refineboxsize']
		apix = self.params['apix']
		rapix = self.params['refineapix']
		npart = self.params['numpart']
		nvol = self.params['num_volumes']
#		sym = self.params['sym']
		sym = "c1"
		psym = self.params['presumed_sym']
		first = self.params['firstimage']
		nws = self.params['non_weighted_sequence']
		threes = self.params['threes']
		lmask = self.params['linmask']
		asqfilt = self.params['asqfilt']
		anginc = self.params['ang_inc']
		keep_ordered = self.params['keep_ordered_num']
		hamwin = self.params['ham_win']
		useEMAN1 = self.params['useEMAN1']
		ipv = self.params['images_per_volume']
		lp = self.params['3d_lpfilt']
		nref = self.params['nref']
		PCA = self.params['PCA']
		neigens = self.params['numeigens']
		recalc = self.params['recalculate']
		preftype = self.params['preftype']
		mrad = self.params['mask_radius']
		irad = self.params['inner_radius']
		orad = self.params['outer_radius']
		tnproc = self.params['threadnproc']
		nproc = self.params['nproc']
		oldavgs = self.params['oldavgs']
		avgs = os.path.join(self.params['rundir'], self.params['avgs'])
		start = self.params['start_at']
				
		#############            copy to working directory          ############
		
		if not os.path.isfile(os.path.join(avgs)[:-4]+".hed"):
			shutil.copyfile(os.path.join(oldavgs[:-4]+".hed"), avgs[:-4]+".hed")				
		if not os.path.isfile(os.path.join(avgs)[:-4]+".img"):
			shutil.copyfile(os.path.join(oldavgs[:-4]+".img"), avgs[:-4]+".img")				
		if self.params['ravgs'] is not None:
			ravgs = os.path.join(self.params['rundir'], self.params['ravgs'])
			if not os.path.isfile(self.params['ravgs'][:-4]+".hed"):
				shutil.copy(self.params['oldravgs'][:-4]+".hed", 
					os.path.join(self.params['ravgs'][:-4]+".hed"))
			if not os.path.isfile(self.params['ravgs'][:-4]+".img"):
				shutil.copy(self.params['oldravgs'][:-4]+".img", 
					os.path.join(self.params['ravgs'][:-4]+".img"))			
			### Euler jumper assessment does not make sense when refine images are different
			ejassess = False 
		else:
			ravgs = avgs
			ejassess = True
						
		###########    scale & prealign class averages, if specified   #########
		
		if self.params['scale'] is True:
			emancmd = "proc2d %s %s_scaled.img scale=%.3f clip=%i,%i edgenorm" \
				% (avgs, avgs[:-4], self.scalefactor, 64, 64)
			avgs = avgs[:-4]+"_scaled.img"
			if start == "none":
				while os.path.isfile(avgs):
					apFile.removeStack(avgs)
				apParam.runCmd(emancmd, "EMAN")
			else:
				apDisplay.printColor("skipping stack scaling", "cyan")
		if self.imagicroot is not None and useEMAN1 is False:
			apIMAGIC.takeoverHeaders(avgs, npart, box)
		
		if self.imagicroot is not None:
			if self.params['prealign'] is True:
				if start == "none":
					avgs = apIMAGIC.prealignClassAverages(rundir, avgs)
					apIMAGIC.checkLogFileForErrors(
						os.path.join(rundir, "prealignClassAverages.log"))

		### select between EMAN1 and IMAGIC for common lines	
		if self.imagicroot is not None and useEMAN1 is False:
			commonlinesdir = os.path.join(rundir, "angular_reconstitution")
		else:
			commonlinesdir = os.path.join(rundir, "cross_common_lines")

		### make links & calculate CCC matrix for 2D averages
		apDisplay.printColor("Calculating similarity matrix", "cyan")
		ccc_matrix = apCommonLines.calculate_ccc_matrix_2d(avgs)
		clsavgs = os.path.split(avgs)[1][:-4]
		if not os.path.isdir(commonlinesdir):
			os.mkdir(commonlinesdir)
		if os.path.islink(os.path.join(commonlinesdir, clsavgs+".hed")):
			os.system("rm -rf %s" % os.path.join(commonlinesdir, clsavgs+".hed"))
		os.symlink(os.path.join(rundir, clsavgs+".hed"), 
			os.path.join(commonlinesdir, clsavgs+".hed"))
		if os.path.islink(os.path.join(commonlinesdir, clsavgs+".img")):
			os.system("rm -rf %s" % os.path.join(commonlinesdir, clsavgs+".img"))
		os.symlink(os.path.join(rundir, clsavgs+".img"), 
			os.path.join(commonlinesdir, clsavgs+".img"))

		##################      create multiple 3d0s       #####################
		
		if start == "none":
			if self.imagicroot is not None and useEMAN1 is False:
				cmdlist = []
				seqfile = open(os.path.join(rundir, 
					"sequences_for_angular_reconstitution.dat"), "w")
				apDisplay.printColor("Running multiple raw volume calculations", "cyan")
				for i in range(nvol):
					sequence = apCommonLines.calculate_sequence_of_addition(avgs, npart, 
						ccc_matrix, first=first, normlist=False, non_weighted_sequence=nws)
					apCommonLines.check_for_duplicates_in_sequence(sequence)
					seqfile.write(str(sequence)+"\n")
					### create IMAGIC batch file for each model & append them to be threaded
					batchfile = apCommonLines.imagic_batch_file(sequence, i+1, avgs, sym, 
						asqfilt, lmask, apix, box, anginc, keep_ordered, hamwin, lp, 
						threes=threes, do_not_remove=False)
					proc = subprocess.Popen('chmod 755 '+batchfile, shell=True)
					proc.wait()
					cmdlist.append(batchfile)
					os.chdir(rundir)
				seqfile.close()
				apThread.threadCommands(cmdlist, nproc=tnproc, pausetime=10)
		
				### check for errors after execution
				for i in range(nvol):
					apIMAGIC.checkLogFileForErrors(
						os.path.join(commonlinesdir, "3d"+str(i+1)+".log"))
			else:
				### use EMAN1 cross-common lines
				cmdlist = []
				seqfile = open(os.path.join(rundir, "sequences_for_cross_common_lines.dat"), "w")
				for i in range(nvol):
					sequence = apCommonLines.calculate_sequence_of_addition(avgs, npart, 
						ccc_matrix, first=first, normlist=False, non_weighted_sequence=nws)
					apCommonLines.check_for_duplicates_in_sequence(sequence)
					seqfile.write(str(sequence)+"\n")
					vol_avgfile = os.path.join(commonlinesdir, "vol_%d_averages.hed" % (i+1))
					vol_seqfile = os.path.join(commonlinesdir, "vol_%d_averages.txt" % (i+1))
					vsf = open(vol_seqfile, "w")
					for j in range(ipv):
						vsf.write("%d\n" % sequence[j])
					vsf.close()
					tmpdir = os.path.join(commonlinesdir, "tmp%d" % (i+1))				
					fullcmd = "proc2d %s %s list=%s ; " % (avgs, vol_avgfile, vol_seqfile)
					fullcmd+= "rm -rf %s ; mkdir %s ; cd %s ; " % (tmpdir, tmpdir, tmpdir)
					fullcmd+= "startAny %s sym=c1 proc=1 rounds=2 mask=%d ; " \
						% (vol_avgfile, mrad/apix)
					fullcmd+= "mv threed.0a.mrc ../threed_%d.mrc ; " % (i+1)
					fullcmd+= "mv CCL.hed ../CCL_%d.hed ; " % (i+1)
					fullcmd+= "mv CCL.img ../CCL_%d.img ; " % (i+1)
					cmdlist.append(fullcmd)
				seqfile.close()
				apThread.threadCommands(cmdlist, nproc=tnproc, pausetime=10)	
				for i in range(nvol):
					shutil.rmtree(os.path.join(commonlinesdir,	"tmp%d" % (i+1)))		
		else:
			apDisplay.printColor("skipping common lines volume calculations", "cyan")
			
		###############     move 3-D models volume directory    ################
		
		### create volume directory
		volumedir = os.path.join(rundir, "volumes")
		if not os.path.isdir(volumedir):
			os.mkdir(volumedir)
		volumes = {}
		cmds = []
		if start == "none":
			apDisplay.printColor("moving volumes for Xmipp 3-D Maximum Likelihood", "cyan")
		for i in range(nvol):
			if useEMAN1 is False:
				volume1 = os.path.join(commonlinesdir, "3d%d_ordered%d_filt.vol" % (i+1,i+1))
			else:
				volume1 = os.path.join(commonlinesdir, "threed_%d.mrc" % (i+1))
			volume2 = os.path.join(volumedir, "3d%d.vol" % (i+1))
			if start == "none":
				if useEMAN1 is False:
					shutil.move(volume1, volume2)
				else:
					cmds.append("proc3d %s %s spidersingle" % (volume1, volume2))
			volumes[(i+1)] = volume2		
		apThread.threadCommands(cmds, nproc=tnproc)
		
		####################          align 3-D models        ##################

		if start == "3D_align" or start == "none":
#		if start != "3D_assess" and start != "3D_refine":		
			### run Maximum Likelihood 3-D alignment & align resulting volumes
			apDisplay.printColor("Running Xmipp maximum likelihood 3-D alignment", "cyan")
			vol_doc_file, alignref = apCommonLines.xmipp_max_like_3d_align(
				volumes, nproc, tnproc, nref)
			alignparams = apCommonLines.read_vol_doc_file(vol_doc_file, nvol)
			apDisplay.printColor("Aligning volumes based on 3-D ML parameters", "cyan")
			apCommonLines.align_volumes(alignparams, alignref, nvol, tnproc, apix)
		else:
			apDisplay.printColor("skipping 3D alignment", "cyan")
			vol_doc_file, alignref = apCommonLines.findAlignmentParams(
				os.path.join(rundir,"max_like_alignment"), nref)
			alignparams = apCommonLines.read_vol_doc_file(vol_doc_file, nvol)

		#####################      Principal Component Analysis   ##############
		
		apDisplay.printColor("Calculating inter-volume similarity", "cyan")
		aligned_volumes = {}
		for i in range(nvol):
			aligned_volumes[(i+1)] = os.path.join(rundir, "volumes", "3d%d.vol" % (i+1))
#			aligned_volumes[(i+1)] = os.path.join(rundir, "volumes", "3d%d.mrc" % (i+1))
		if PCA is True:
			simfile, sim_matrix = apCommonLines.runPrincipalComponentAnalysis(
				aligned_volumes, nvol, neigens, box, apix, recalculate=recalc)
		else:
			simfile, sim_matrix = apCommonLines.calculate_ccc_matrix_3d(
				aligned_volumes, nvol)	

		################            3-D affinity propagation       #############

		### 3-D Affinity Propagation
		apDisplay.printColor("Averaging volumes with Affinity Propagation", "cyan")
		preffile = apCommonLines.set_preferences(sim_matrix, preftype, nvol)
		classes = apCommonLines.run_affinity_propagation(aligned_volumes, simfile, 
			preffile, box, apix)

		#########    refine volumes using Xmipp projection matching    #########

		if start == "3D_align" or start == "3D_refine" or start == "none":
#		if start != "3D_assess":
			if not os.path.isdir("refinement"):
				os.mkdir("refinement")
			os.chdir("refinement")
			apXmipp.breakupStackIntoSingleFiles(ravgs)
			xmippcmd = "xmipp_normalize -i partlist.sel -method OldXmipp"
			apParam.runCmd(xmippcmd, "Xmipp")
			for i in classes.keys():
				emancmd = "proc3d %s %s scale=%.3f clip=%d,%d,%d mask=%s spidersingle" \
					% (os.path.join(rundir, "%d.mrc" % i), "%d.vol" % i, \
						(1/self.scalefactor), rbox, rbox, rbox, (mrad / rapix))
				apParam.runCmd(emancmd, "EMAN")
				apCommonLines.refine_volume(rundir, ravgs, i, mrad, irad, orad, rapix, nproc)
				emancmd = "proc3d %s %s apix=%.3f" \
					% (os.path.join("refine_%d" % i, "3d%d_refined.vol" % i), \
						os.path.join(rundir, "%d_r.mrc" % i), rapix)
				apParam.runCmd(emancmd, "EMAN")
			os.chdir(rundir)
		else:
			apDisplay.printColor("skipping 3D refinement", "cyan")			
		
		#################            model evaluation           ################
		
		if start == "3D_align" or start == "3D_refine" or start == "3D_assess" or start == "none":
#		if start == "none" or start=="3D_assess":
			### final model assessment
			try:
				euler_array = apCommonLines.getEulerValuesForModels(alignparams, 
					rundir, nvol, npart, threes=threes)
			except:
				euler_array = None
				ejassess = False
			if refine is True:
				apCommonLines.assess_3Dclass_quality2(rundir, aligned_volumes, sim_matrix, 
					classes, euler_array, box, rbox, rapix, ravgs, psym, npart, ejassess=ejassess)
			else:
				apCommonLines.assess_3Dclass_quality(rundir, aligned_volumes, sim_matrix, 
					classes, euler_array, box, apix, avgs, psym, npart, ejassess=ejassess)
			apCommonLines.combineMetrics("final_model_stats.dat", 
				"final_model_stats_sorted_by_Rcrit.dat", **{"CCPR":(1,1)})


		##################          upload & cleanup          ##################

		### upload to database, if specified
		self.upload()
		
		### make chimera snapshots
		if refine is True:
			for i in classes.keys():
				if self.params['mass'] is not None:
					apChimera.filterAndChimera(
						os.path.join(self.params['rundir'], "%d_r.mrc" % i),
						res=self.params['3d_lpfilt'],
						apix=self.params['refineapix'],
						box=self.params['refineboxsize'],
						chimtype="snapshot",
						contour=2,
						zoom=1,
						sym="c1",
						color="gold",
						mass=self.params['mass']
						)
	
		### cleanup
		snapshots = glob.glob("*.png")
		mtlfiles = glob.glob("*.mtl")
		objfiles = glob.glob("*.obj")
		pyfiles = glob.glob("*mrc.py")
		for file in mtlfiles:
			os.remove(file)
		for file in objfiles:
			os.remove(file)
		for file in pyfiles:
			os.remove(file)
		if not os.path.isdir("snapshots"):
			os.mkdir("snapshots")
		for s in snapshots:
			shutil.move(s, os.path.join("snapshots", s))
			

if __name__ == "__main__":

	ACL = OptiMod()
	ACL.start()
	ACL.close()
	
	
