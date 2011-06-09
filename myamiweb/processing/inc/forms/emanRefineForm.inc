<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "basicRefineForm.inc";


class EmanRefineForm extends BasicRefineForm 
{
	public function getMethodType() { return "eman"; }
	public function createFormParams() { return new EmanParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// display form title
		echo"
	    <br />
	    <H4>EMAN Reconstruction Parameters</H4>
	    <hr />";

		$shortSize = 4;
		$longSize = 20;
		echo $this->insertTextField( $params["imask"]["name"], $params["imask"]["label"], $params["imask"]["value"], $longSize, $params["imask"]["enable"] );
		echo $this->insertTextField( $params["amask"]["name"], $params["amask"]["label"], $params["amask"]["value"], $longSize, $params["amask"]["enable"] );
		echo $this->insertTextField( $params["maxshift"]["name"], $params["maxshift"]["label"], $params["maxshift"]["value"], $longSize, $params["maxshift"]["enable"] );
		echo $this->insertTextField( $params["hard"]["name"], $params["hard"]["label"], $params["hard"]["value"], $longSize, $params["hard"]["enable"] );
		echo $this->insertTextField( $params["clskeep"]["name"], $params["clskeep"]["label"], $params["clskeep"]["value"], $longSize, $params["clskeep"]["enable"] );
		echo $this->insertTextField( $params["clsiter"]["name"], $params["clsiter"]["label"], $params["clsiter"]["value"], $longSize, $params["clsiter"]["enable"] );
		echo $this->insertTextField( $params["xfiles"]["name"], $params["xfiles"]["label"], $params["xfiles"]["value"], $longSize, $params["xfiles"]["enable"] );
		echo $this->insertTextField( $params["shrink"]["name"], $params["shrink"]["label"], $params["shrink"]["value"], $longSize, $params["shrink"]["enable"] );
		echo $this->insertTextField( $params["euler2"]["name"], $params["euler2"]["label"], $params["euler2"]["value"], $longSize, $params["euler2"]["enable"] );
		echo $this->insertTextField( $params["median"]["name"], $params["median"]["label"], $params["median"]["value"], $longSize, $params["median"]["enable"] );
		echo $this->insertTextField( $params["phscls"]["name"], $params["phscls"]["label"], $params["phscls"]["value"], $longSize, $params["phscls"]["enable"] );
		echo $this->insertTextField( $params["refine"]["name"], $params["refine"]["label"], $params["refine"]["value"], $longSize, $params["refine"]["enable"] );
		echo $this->insertTextField( $params["tree"]["name"], $params["tree"]["label"], $params["tree"]["value"], $longSize, $params["tree"]["enable"] );
		
		echo "<br />\n";
		echo "<b>Coran parameters</b>\n";
		echo "<br />\n";
		
		echo $this->insertTextField( $params["coranCC"]["name"], $params["coranCC"]["label"], $params["coranCC"]["value"], $longSize, $params["coranCC"]["enable"] );
		echo $this->insertTextField( $params["coranmask"]["name"], $params["coranmask"]["label"], $params["coranmask"]["value"], $longSize, $params["coranmask"]["enable"] );
		echo $this->insertTextField( $params["coranlp"]["name"], $params["coranlp"]["label"], $params["coranlp"]["value"], $longSize, $params["coranlp"]["enable"] );
		echo $this->insertTextField( $params["coranhp"]["name"], $params["coranhp"]["label"], $params["coranhp"]["value"], $longSize, $params["coranhp"]["enable"] );
		echo $this->insertTextField( $params["coranhcc"]["name"], $params["coranhcc"]["label"], $params["coranhcc"]["value"], $longSize, $params["coranhcc"]["enable"] );
								
		echo "<br/>\n";		
	}
	
	public function buildCommand( $params )
	{		
		$command = 'prepEman.py ';
		$command.= '--ang='.$params["angSampRate"]["value"].' ';
		$command.= '--mask='.$params["outerMaskRadius"]["value"].' ';
		$command.= '--sym='.$params["symmetry"]["value"].' ';
		$command.= '--imask='.$params["imask"]["value"].' ';
		$command.= '--amask='.$params["amask"]["value"].' ';		
		$command.= '--maxshift='.$params["maxshift"]["value"].' ';
		$command.= '--hard='.$params["hard"]["value"].' ';
		$command.= '--clskeep='.$params["clskeep"]["value"].' ';
		$command.= '--clsiter='.$params["clsiter"]["value"].' ';
		$command.= '--xfiles='.$params["xfiles"]["value"].' ';
		$command.= '--shrink='.$params["shrink"]["value"].' ';
		$command.= '--euler2='.$params["euler2"]["value"].' ';
		$command.= '--median='.$params["median"]["value"].' ';
		$command.= '--phscls='.$params["phscls"]["value"].' ';
		$command.= '--refine='.$params["refine"]["value"].' ';
		$command.= '--tree='.$params["tree"]["value"].' ';
		$command.= '--coranCC='.$params["coranCC"]["value"].' ';
		$command.= '--coranmask='.$params["coranmask"]["value"].' ';
		$command.= '--coranlp='.$params["coranlp"]["value"].' ';
		$command.= '--coranhp='.$params["coranhp"]["value"].' ';
		$command.= '--coranhcc='.$params["coranhcc"]["value"].' ';	
		
		if ($params["filterEstimated"]["value"]=='on')
			$command.= '--filt3d='.$params["filterResolution"]["value"].' ';
		
		return $command;
	}
	
	protected function setImportParams()
	{
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'Mostly asymmetric particle';
		$outerMaskRadius 	= '126';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= 'd7'; 
		$numIters 			= '9'; 
		$angSampRate 		= '3x10:3x8:3x6';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$imask				= ''; 
		$amask				= '';
		$maxshift			= '';
		$hard				= '25';
		$clskeep			= '0.8';
		$clsiter			= '2x8:1x3:2x8:1x3:2x8:1x3'; 
		$xfiles				= '';
		$shrink				= '';
		$euler2				= '';
		$median				= '';
		$phscls				= '9x1';
		$refine				= '6x0:3x1';
		$tree				= '';
		$coranCC			= '';
		$coranmask			= '';
		$coranlp			= '';
		$coranhp			= '';
		$coranhcc			= '';
		
		$asymmSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $asymmSet );

		$id 				= 'groel1';
		$label 				= 'GroEL with 10,000+ particles';
		$numIters 			= '20'; 
		$angSampRate 		= '4x5:4x4:4x3:4x2:4x1';
		$clsiter			= '2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3'; 
		$refine				= '16x0:4x1';
		$groelSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $groelSet );
		
		$id 				= 'virusgood';
		$label 				= 'Icos Virus with good starting model';
		$numIters 			= '14'; 
		$angSampRate 		= '4x3:4x2:3x1:3x0.8';
		$clsiter			= '2x8:2x3:2x8:8x3'; 
		$refine				= '11x0:3x1';
		$virusSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $virusSet );
	}
}


// extend the RefineFormParameters class to add the EMAN 
// advanced parameter default values. 
class EmanParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$imask='', $amask='', $maxshift='', $hard='', $clskeep='',
							$clsiter='', $xfiles='', $shrink='', $euler2='', $median='', $phscls='', $refine='', 
							$tree='', $coranCC='', $coranmask='', $coranlp='', $coranhp='', $coranhcc='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "imask", $imask, "imask" );
		$this->addParam( "amask", $amask, "amask" );		
		$this->addParam( "maxshift", $maxshift, "maxshift " );
		$this->addParam( "hard", $hard, "hard" );
		$this->addParam( "clskeep", $clskeep, "clskeep" );
		$this->addParam( "clsiter", $clsiter, "clsiter" );
		$this->addParam( "xfiles", $xfiles, "xfiles" );
		$this->addParam( "shrink", $shrink, "shrink" );
		$this->addParam( "euler2", $euler2, "euler2" );
		$this->addParam( "median", $median , "median " );
		$this->addParam( "phscls", $phscls, "phscls" );
		$this->addParam( "refine", $refine, "refine" );
		$this->addParam( "tree", $tree, "tree" );
		$this->addParam( "coranCC", $coranCC, "CC cut" );
		$this->addParam( "coranmask", $coranmask, "Mask" );
		$this->addParam( "coranlp", $coranlp, "LP" );
		$this->addParam( "coranhp", $coranhp, "HP" );
		$this->addParam( "coranhcc", $coranhcc, "HaCC" );
		
		// disable any general params that do not apply to this method
		$this->disableParam("outerAlignRadius");
		$this->disableParam("innerAlignRadius");
		$this->disableParam("filterComputed");
	}
	
	function validate() 
	{
		$parentMsg = parent::validate();
		
		$validator = new formValidator();
		 
		$validator->addValidation($this->params["outerMaskRadius"]["name"], $this->params["outerMaskRadius"]["value"], "req", "Enter an outer mask radius.");
		$validator->addValidation($this->params["symmetry"]["name"], $this->params["symmetry"]["value"], "req", "Enter symmetry.");
		$validator->addValidation($this->params["angSampRate"]["name"], $this->params["angSampRate"]["value"], "req", "Enter angular sampling rate.");
		
		$validator->runValidation();
		$msg = $validator->getErrorMessage();	
		
		$errMsg = array_merge( $parentMsg, $msg );
		
		// TODO: if amask is used, then xfiles must also be used
//		if ($_POST['amask1'.$i] || $_POST['amask2'.$i] || $_POST['amask3'.$i]) {
//			if (!($_POST['amask1'.$i] && $_POST['amask2'.$i] && $_POST['amask3'.$i]))
//				jobForm("ERROR: All 3 amask values of amask must be entered for iteration $i");
//			if (!$_POST['xfiles'.$i])
//				jobForm("ERROR: amask requires the use of xfiles for iteration $i");
//		}
		
		
		return $errMsg;
	}
}

?>
