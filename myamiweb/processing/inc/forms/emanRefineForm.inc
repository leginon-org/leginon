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
		echo $params->insertTextField( "imask", $longSize );
		echo $params->insertTextField( "amask", $longSize );
		echo $params->insertTextField( "maxshift", $longSize );
		echo $params->insertTextField( "hard", $longSize );
		echo $params->insertTextField( "clskeep", $longSize );
		echo $params->insertTextField( "clsiter", $longSize );
		echo $params->insertTextField( "xfiles", $longSize );
		echo $params->insertTextField( "shrink", $longSize );
		echo $params->insertTextField( "euler2", $longSize );
		echo $params->insertTextField( "median", $longSize );
		echo $params->insertTextField( "phscls", $longSize );
		echo $params->insertTextField( "refine", $longSize );
		echo $params->insertTextField( "tree", $longSize );
		
		echo "<br />\n";
		echo "<b>Coran parameters</b>\n";
		echo "<br />\n";
		
		echo $params->insertTextField( "coranCC", $longSize );
		echo $params->insertTextField( "coranmask", $longSize );
		echo $params->insertTextField( "coranlp", $longSize );
		echo $params->insertTextField( "coranhp", $longSize );
		echo $params->insertTextField( "coranhcc", $longSize );
								
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

		// add parameter requirements
		$this->addValidation( "outerMaskRadius", "req" );
		$this->addValidation( "symmetry", "req" );
		$this->addValidation( "angSampRate", "req" );
	}
	
	function validate() 
	{
		$msg = parent::validate();
		
		
		// TODO: if amask is used, then xfiles must also be used
//		if ($_POST['amask1'.$i] || $_POST['amask2'.$i] || $_POST['amask3'.$i]) {
//			if (!($_POST['amask1'.$i] && $_POST['amask2'.$i] && $_POST['amask3'.$i]))
//				jobForm("ERROR: All 3 amask values of amask must be entered for iteration $i");
//			if (!$_POST['xfiles'.$i])
//				jobForm("ERROR: amask requires the use of xfiles for iteration $i");
//		}
		
		
		return $msg;
	}
}

?>
