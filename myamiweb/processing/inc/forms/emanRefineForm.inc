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
	public function createFormParams() { return new EmanParams(); }
	
	protected function setPublications()
	{
		$this->pubKeyList = array("eman");
	}
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "eman" );		
		
		$shortSize = 4;
		$longSize = 20;
		$html .= $params->insertTextField( "imask", $longSize );
		$html .= $params->insertTextField( "amask1", $longSize, '', "eman.amask" );
		$html .= $params->insertTextField( "amask2", $longSize, '', "eman.amask" );
		$html .= $params->insertTextField( "amask3", $longSize, '', "eman.amask" );
		$html .= $params->insertTextField( "maxshift", $longSize );
		$html .= $params->insertTextField( "hard", $longSize );
		$html .= $params->insertTextField( "classkeep", $longSize );
		$html .= $params->insertTextField( "classiter", $longSize );
		$html .= $params->insertTextField( "xfiles", $longSize );
		$html .= $params->insertTextField( "shrink", $longSize );
		$html .= $params->insertTextField( "euler2", $longSize );
		$html .= $params->insertTextField( "median", $longSize );
		$html .= $params->insertTextField( "phasecls", $longSize );
		$html .= $params->insertTextField( "refine", $longSize );
		$html .= $params->insertTextField( "tree", $longSize );
		
		$html .= "<br />\n";
		$html .= "<b>Coran parameters</b>\n";
		$html .= "<br />\n";
		
		$html .= $params->insertTextField( "coranCC", $longSize );
		$html .= $params->insertTextField( "coranmask", $longSize );
		$html .= $params->insertTextField( "coranlp", $longSize );
		$html .= $params->insertTextField( "coranhp", $longSize );
		$html .= $params->insertTextField( "coranhcc", $longSize );
								
		$html .= "<br/>\n";		
		
		return $html;
	}
	
	public function buildCommand( $postArray )
	{		
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = '';
		$command = $this->addCommandFlag( $command, "angSampRate" );
		$command = $this->addCommandFlag( $command, "outerMaskRadius" );
		$command = $this->addCommandFlag( $command, "innerMaskRadius" );
		$command = $this->addCommandFlag( $command, "symmetry" );
		$command = $this->addCommandFlag( $command, "endIter" );
		$command = $this->addCommandFlag( $command, "imask" );
		$command = $this->addCommandFlag( $command, "maxshift" );
		$command = $this->addCommandFlag( $command, "hard" );
		$command = $this->addCommandFlag( $command, "classkeep" );
		$command = $this->addCommandFlag( $command, "classiter" );
		$command = $this->addCommandFlag( $command, "xfiles" );
		$command = $this->addCommandFlag( $command, "shrink" );
		$command = $this->addCommandFlag( $command, "euler2" );
		$command = $this->addCommandFlag( $command, "median" );
		$command = $this->addCommandFlag( $command, "phasecls" );
		$command = $this->addCommandFlag( $command, "refine" );
		$command = $this->addCommandFlag( $command, "tree" );
		$command = $this->addCommandFlag( $command, "coranCC" );
		$command = $this->addCommandFlag( $command, "coranmask" );
		$command = $this->addCommandFlag( $command, "coranlp" );
		$command = $this->addCommandFlag( $command, "coranhp" );
		$command = $this->addCommandFlag( $command, "coranhcc" );
		
		if ($params->getParamValue("filterEstimated") == 'on') {
			$command = $this->addCommandFlag( $command, "filt3d", "filterResolution" );
		}
		
		// add the amask values if they are set
		$amask1 = $params->getParamValue("amask1");
		$amask2 = $params->getParamValue("amask2");
		$amask3 = $params->getParamValue("amask3");
		if ( $amask1 && $amask2 && $amask3 ) {
			$array = array($amask1, $amask2, $amask3);
			$amaskvalue = implode(",", $array);			
			$command = $this->addCommandFlag( $command, "amask", '', $amaskvalue );
		}
			
		return $command;
	}
	
	protected function setImportParams()
	{
		$sym = $this->getSymmetry();
		
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'Mostly asymmetric particle';
		$outerMaskRadius 	= '126'; //TODO: this should not be hard coded???
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= $sym; 
		$endIter 			= '9'; 
		$angSampRate 		= '3x10:3x8:3x6';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$imask				= ''; 
		$amask1				= '';
		$amask2				= '';
		$amask3				= '';
		$maxshift			= '';
		$hard				= '25';
		$classkeep			= '0.8';
		$classiter			= '2x8:1x3:2x8:1x3:2x8:1x3'; 
		$xfiles				= '';
		$shrink				= '';
		$euler2				= '';
		$median				= '';
		$phasecls			= '9xt';
		$refine				= '6xf:3xt';
		$tree				= '';
		$coranCC			= '';
		$coranmask			= '';
		$coranlp			= '';
		$coranhp			= '';
		$coranhcc			= '';
		
		$asymmSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask1, $amask2, $amask3, $maxshift, $hard, $classkeep,
							$classiter, $xfiles, $shrink, $euler2, $median, $phasecls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $asymmSet );

		$id 				= 'groel1';
		$label 				= 'GroEL with 10,000+ particles';
		$endIter 			= '20'; 
		$angSampRate 		= '4x5:4x4:4x3:4x2:4x1';
		$classiter			= '2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3'; 
		$refine				= '16xf:4xt';
		$groelSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask1, $amask2, $amask3, $maxshift, $hard, $classkeep,
							$classiter, $xfiles, $shrink, $euler2, $median, $phasecls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $groelSet );
		
		$id 				= 'virusgood';
		$label 				= 'Icos Virus with good starting model';
		$endIter 			= '14'; 
		$angSampRate 		= '4x3:4x2:3x1:3x0.8';
		$classiter			= '2x8:2x3:2x8:8x3'; 
		$refine				= '11xf:3xt';
		$virusSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask1, $amask2, $amask3, $maxshift, $hard, $classkeep,
							$classiter, $xfiles, $shrink, $euler2, $median, $phasecls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $virusSet );
	}
	
	protected function addImportedRefineIter( $paramSet, $iter ) 
	{
		$paramSet->addIterationToValue( "angSampRate", $iter['ang'] );
		$paramSet->addIterationToValue( "amask1", $iter['EMAN_amask1'] );
		$paramSet->addIterationToValue( "amask2", $iter['EMAN_amask2'] );
		$paramSet->addIterationToValue( "amask3", $iter['EMAN_amask3'] );
		$paramSet->addIterationToValue( "maxshift", $iter['EMAN_maxshift'] );
		$paramSet->addIterationToValue( "hard", $iter['EMAN_hard'] );
		$paramSet->addIterationToValue( "classiter", $iter['EMAN_classiter'] );
		$paramSet->addIterationToValue( "classkeep", $iter['EMAN_classkeep'] );
		$paramSet->addIterationToValue( "filterResolution", $iter['EMAN_filt3d'] );
		$paramSet->addIterationToValue( "shrink", $iter['EMAN_shrink'] );
		$paramSet->addIterationToValue( "euler2", $iter['EMAN_euler2'] );
		$paramSet->addIterationToValue( "xfiles", $iter['EMAN_xfiles'] );
		$paramSet->addIterationToValue( "median", ($iter['EMAN_median']) ? 't' : 'f' );
		$paramSet->addIterationToValue( "phasecls", ($iter['EMAN_phasecls']) ? 't' : 'f' );
		$paramSet->addIterationToValue( "refine", ($iter['EMAN_refine']) ? 't' : 'f' );
		$paramSet->addIterationToValue( "coran", ($iter['postRefineClassAverages']) ? 't' : 'f' );
	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		$stackInfo = $this->getStackInfo();
		$box = $stackInfo['boxsize'];
		$apix = $stackInfo['apix'];
		$sym = $this->getSymmetry();
		
		$radPix = ($box/2)-2;
		$radAng = round($radPix * $apix);
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      obj.outerMaskRadius.value = $radAng;
	      obj.innerMaskRadius.value = 0;
	      obj.angSampRate.value = '4x10:2x5:2x3:2x2';
	      obj.symmetry.value = '$sym';
	      obj.endIter.value = '10';
	      obj.percentDiscard.value = '10';
	      obj.filterEstimated.checked = false;
	      obj.filterResolution.value = '';
	      obj.imask.value = '';
	      obj.amask1.value = '';		
	      obj.amask2.value = '';		
	      obj.amask3.value = '';		
	      obj.maxshift.value = '';
	      obj.hard.value = '25';
	      obj.classkeep.value = '0.8';
	      obj.classiter.value = '8';
	      obj.xfiles.value = '';
	      obj.shrink.value = '';
	      obj.euler2.value = '';
	      obj.median.value = '';
	      obj.phasecls.value = '10xt';
	      obj.refine.value = '';
	      obj.tree.value = '';
	      obj.coranCC.value = '';
	      obj.coranmask.value = '';
	      obj.coranlp.value = '';
	      obj.coranhp.value = '';
	      obj.coranhcc.value = '';	      
	      return;
	    }
	  </SCRIPT>\n";
		return $javafunc;
	}
	
}


// extend the RefineFormParameters class to add the EMAN 
// advanced parameter default values. 
class EmanParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$imask='', $amask1='', $amask2='', $amask3='', $maxshift='', $hard='', $classkeep='',
							$classiter='', $xfiles='', $shrink='', $euler2='', $median='', $phasecls='', $refine='', 
							$tree='', $coranCC='', $coranmask='', $coranlp='', $coranhp='', $coranhcc='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		// TODO: amask1-amask3
		$this->addParam( "imask", $imask, "imask" );
		$this->addParam( "amask1", $amask1, "amask1" );		
		$this->addParam( "amask2", $amask2, "amask2" );		
		$this->addParam( "amask3", $amask3, "amask3" );		
		$this->addParam( "maxshift", $maxshift, "maxshift " );
		$this->addParam( "hard", $hard, "hard" );
		$this->addParam( "classkeep", $classkeep, "classkeep" );
		$this->addParam( "classiter", $classiter, "classiter" );
		$this->addParam( "xfiles", $xfiles, "xfiles" );
		$this->addParam( "shrink", $shrink, "shrink" );
		$this->addParam( "euler2", $euler2, "euler2" );
		$this->addParam( "median", $median , "median " );
		$this->addParam( "phasecls", $phasecls, "phasecls" );
		$this->addParam( "refine", $refine, "refine" );
		$this->addParam( "tree", $tree, "tree" );
		$this->addParam( "coranCC", $coranCC, "CC cut" );
		$this->addParam( "coranmask", $coranmask, "Mask" );
		$this->addParam( "coranlp", $coranlp, "LP" );
		$this->addParam( "coranhp", $coranhp, "HP" );
		$this->addParam( "coranhcc", $coranhcc, "HaCC" );
		
		// hide any general params that do not apply to this method
		$this->hideParam("outerAlignRadius");
		$this->hideParam("innerAlignRadius");
		$this->hideParam("filterComputed");
		$this->hideParam("filterConstant");
		
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
