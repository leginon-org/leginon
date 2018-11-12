<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "basicRefineForm.inc";


class FrealignRefineForm extends BasicRefineForm 
{
	// return an instance of this refine forms parameter class which is 
	// an extension of the FormParameters class.
	public function createFormParams() { return new FrealignParams(); }

	// Add to the pubKeyList any publications that should be referenced by papers using this method.
	// The keys added here must match the ones found in the publicationList.inc file.
	protected function setPublications()
	{
		$this->pubKeyList = array("frealign");
	}
	
	// This is where an html form for this recon method's specific parameters is defined. 
	// Returns html. 
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$paramSet = $this->getFormParams();
		
		// make sure we are using the appropriate pop-up help messages
		$paramSet->setHelpSection( "frealign" );	
			
		// set field sizes
		$shortSize = 4;
		
		// display form title
		$html .= "
	    <br />
	    <H4>Frealign Processing Parameters</H4>
	    <hr />";
				
		// find each stack entry in database
// This section is commented out for now until we support more features of Frealign
//		$reconstackid = $paramSet->getParamValue( 'reconstackid' );
//		$stackIds = $this->particle->getStackIds( $_GET['expId'] );
//		if (count($stackIds) > 0) {
//			$html .=  "<br />\n";
//			$html .=  "<b>Select Reconstruction Stack:</b>\n";
//			$html .=  "<br />\n";
//			$html .=  $this->reconStackSelector($stackIds, $reconstackid);
//			$html .=  "<br />\n";
//		}
//		
//		// TODO: add javascript so that this updates when a stack is selected
//		if ( $reconstackid ) {
//			$html .=  stacksummarytable( $reconstackid, true);
//		}				
//		
//		$html .=  "<br />\n";
	
		$html .=  $paramSet->insertCheckboxField( "fmag" );
		$html .=  $paramSet->insertCheckboxField( "fdef" );
		$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
		$html .=  $paramSet->insertCheckboxField( "fpart" );
		$html .=  $paramSet->insertCheckboxField( "fbeaut" );
		$html .=  $paramSet->insertCheckboxField( "ffilt" );
		$html .=  $paramSet->insertCheckboxField( "fbfact" );
		$html .=  $paramSet->insertCheckboxField( "pbc" );
		$html .=  $paramSet->insertTextField( "hp", $shortSize, "(in &Aring;ngstroms)" );
		$html .=  $paramSet->insertTextField( "lp", $shortSize, "(in &Aring;ngstroms)" );
		$html .=  $paramSet->insertTextField( "wgh", $shortSize, "(percent)");
		$html .=  $paramSet->insertTextField( "mw", $shortSize, "(in kD)" );
		// for debugging
		$html .=  $paramSet->insertCheckboxField( "fmatch" );
		// These parameters may be added back in when we add the search feature
		//$html .=  $paramSet->insertTextField( "dang", $shortSize );
		//$html .=  $paramSet->insertTextField( "itmax", $shortSize );
		//$html .=  $paramSet->insertTextField( "ipmax", $shortSize );
				
		$html .=  "<br />\n";
		$html .=  "<b>Refine (MASK):</b>\n";
		$html .=  "<br />\n";
	
		$html .=  $paramSet->insertCheckboxField( "psi" );
		$html .=  $paramSet->insertCheckboxField( "theta" );
		$html .=  $paramSet->insertCheckboxField( "phi" );
		$html .=  $paramSet->insertCheckboxField( "x" );
		$html .=  $paramSet->insertCheckboxField( "y" );
		
								
		return $html;
	}
	
		
	// display a selection box with any valid stacks. 
	// compares stacks to the refine stack previously selected by the user
	function reconStackSelector($stackIds, $stackidval) 
	{	
		$refineStack = $this->getStackInfo();
		
		$html .=  "<SELECT NAME='reconstackid' >\n";
		$html .=  "<OPTION VALUE='' style='color:green;' >Same as refinement</option>\n";
		foreach ($stackIds as $stackid){
			// get number of particles in each stack
			$totalp = $this->particle->getNumStackParticles($stackid['stackid']);
			$nump = $totalp; //commafy($totalp);
			// get pixel size of stack
			$apix = ($this->particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
			// truncated pixel size
			$showapix = sprintf("%.2f",$apix);
			// get box size
			$box = $stackid['boxsize'];
			
			// if this is not a valid stack, don't add it to the list
			if ( $nump != $refineStack['lastPart'] || (string)$apix != $refineStack['apix'] || $box != $refineStack['boxsize'] ) {
				continue;
			}

			$html .=  "<OPTION VALUE='$stackid[stackid]'";
			// select previously set stack on resubmita
			if ($stackid['stackid']==$stackidval) $html .=  " SELECTED";
			$html .= ">$s[shownstackname] ID: $stackid[stackid] ($nump particles, $showapix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
		}
		$html .=  "</SELECT>\n";
		return $html;
	}	
	
	protected function setImportParams()
	{
		$stackInfo 	= $this->getStackInfo();
		$box 		= $stackInfo['boxsize'];
		$apix 		= $stackInfo['apix'];
		$sym 		= $this->getSymmetry();
		
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'asymmetric particles';
		$outerMaskRadius 	= round(($apix*$box/2.0) - (3.0*$apix)); // Nico's formula for beginners
		$innerMaskRadius 	= '0';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= $sym; 
		$endIter 			= '10'; 
		$angSampRate 		= '';
		$percentDiscard 	= '20';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$wgh 				= '0.07';
		$pbc  				= '100';
		$itmax 				= '10';
		$ipmax				= '0';
		$hp 				= '300';
		$lp 				= '10';
		$reconstackid		= '';
		$fmag				= ''; 
		$fdef				= ''; 
		$fpart				= ''; 
		$fbeaut				= ''; 
		$ffilt				= 'CHECKED'; 
		$fbfact				= ''; 
		$psi				= 'CHECKED'; 
		$theta				= 'CHECKED'; 
		$phi				= 'CHECKED'; 
		$x					= 'CHECKED'; 
		$y					= 'CHECKED';
		
		// Create a parameter set with the values defined above.
		$asymmSet = new FrealignParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$wgh, $pbc, $itmax, $ipmax, $hp, $lp, $reconstackid, $dang, 
							$fmag, $fdef, $fpart, $fbeaut, $ffilt, $fbfact, $psi, $theta, $phi, $x, $y );
							
		// Add this param set to the list that shows up in the GUI.
		$this->addDefaultParams( $asymmSet );
	}
		
	// This function is called by the base class when parameters are being imported from a previous refinement.
	protected function addImportedRefineIter( $paramSet, $iter ) 
	{
		$paramSet->addIterationToValue( "wgh", $iter['wgh'] );
		$paramSet->addIterationToValue( "pbc", $iter['pbc'] );
		$paramSet->addIterationToValue( "itmax", $iter['itmax'] );
		$paramSet->addIterationToValue( "ipmax", $iter['ipmax'] );
		$paramSet->addIterationToValue( "cs", $iter['cs'] );
		$paramSet->addIterationToValue( "hp", $iter['highpass'] );
		$paramSet->addIterationToValue( "lp", $iter['lowpass'] );
		$paramSet->addIterationToValue( "fmag", $iter['fmag'] );
		$paramSet->addIterationToValue( "fdef", $iter['fdef'] );
		$paramSet->addIterationToValue( "fpart", $iter['fpart'] );
		$paramSet->addIterationToValue( "fbeaut", $iter['fbeaut'] );
		$paramSet->addIterationToValue( "ffilt", $iter['ffilt'] );
		$paramSet->addIterationToValue( "fbfact", $iter['fbfact'] );
		$paramSet->addIterationToValue( "psi", $iter['psi'] );
		$paramSet->addIterationToValue( "theta", $iter['theta'] );
		$paramSet->addIterationToValue( "phi", $iter['phi'] );
		$paramSet->addIterationToValue( "x", $iter['x'] );
		$paramSet->addIterationToValue( "y", $iter['y'] );
	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		// get the stack info for the stack selected by the user
		$stack 	= $this->getStackInfo();
		$box 	= $stack['boxsize'];
		$apix 	= $stack['apix'];
		$sym = $this->getSymmetry();
		
		// calculate default parameters
		$outerMaskRadius 	= round($apix * $box / 3.0);
		$rrec 				= (ceil($apix * 20)) / 10;
		
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $outerMaskRadius;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = 0;
	      if (obj.symmetry) obj.symmetry.value = '$sym';
	      if (obj.endIter) obj.endIter.value = '10';
	      if (obj.percentDiscard) obj.percentDiscard.value = '15';
	      if (obj.wgh) obj.wgh.value = '0.07';
	      if (obj.pbc) obj.pbc.value = '100';
	      if (obj.itmax) obj.itmax.value = '10';
	      if (obj.ipmax) obj.ipmax.value = '10';
	      if (obj.hp) obj.hp.value = '300';
	      if (obj.lp) obj.lp.value = '10';
	      if (obj.reconstackval) obj.reconstackid.value = '';
	      if (obj.dang) obj.dang.value = '5';
	      if (obj.fmag) obj.fmag.checked = false;
	      if (obj.fdef) obj.fdef.checked = false;
	      if (obj.fpart) obj.fpart.checked = false;
	      if (obj.fbeaut) obj.fbeaut.checked = false;
	      if (obj.ffilt) obj.ffilt.checked = true;
	      if (obj.fbfact) obj.fbfact.checked = false;
	      if (obj.psi) obj.psi.checked = true;
	      if (obj.theta) obj.theta.checked = true;
	      if (obj.phi) obj.phi.checked = true;
	      if (obj.x) obj.x.checked = true;
	      if (obj.y) obj.y.checked = true;
	      
	      return;
	    }
	  </script>\n";
		return $javafunc;
	}
	
	public function buildCommand( $postArray )
	{
		$params = $this->getFormParams();
		//TO DO: fsearch depends on the prepared particle param file
		$params->setParamValue('fsearch','on');

		$command = parent::buildCommand( $postArray );
		return $command;

	}
}

// extend the RefineFormParameters class so that we can add the frealign 
// advanced parameter default values to the web form. 
class FrealignParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$wgh='', $pbc='', $itmax='', $ipmax='', $hp='', $lp='', $reconstackid='', 
							$dang='', $fmag='', $fdef='', $fpart='', $fbeaut='', $ffilt='', $fbfact='', 
							$psi='', $theta='', $phi='', $x='', $y='', $fmatch='CHECKED') 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "wgh", $wgh, "Amplitude contrast (WGH)" );
		$this->addParam( "pbc", $pbc, "Weight particles in reconstruction (PBC)" );
		$this->addParam( "itmax", $itmax, "Number of randomized search trials (ITMAX)" );
		$this->addParam( "ipmax", $ipmax, "Number of potential matches to refine (IPMAX)" );
		$this->addParam( "hp", $hp, "Lower resolution limit or high-pass filter (RMAX1)" );
		$this->addParam( "lp", $lp, "Higher resolution limit or low-pass filter (RMAX2)" );
		$this->addParam( "mw", $hp, "Approximated molecular weight" );
		$this->addParam( "reconstackid", $reconstackid, "Reconstruction Stack" );
		$this->addParam( "dang", $dang, "Angular increment (DANG)" );
		
		// new parameters per Niko's redesign
		$this->addParam( "fmag", $fmag, "Magnification refinement (FMAG)" );
		$this->addParam( "fdef", $fdef, "Defocus refinement (FDEF)" );
		$this->addParam( "fpart", $fpart, "per particle (FPART)" );
		$this->addParam( "fbeaut", $fbeaut, "Apply symmetry in real space (FBEAUT)" );
		$this->addParam( "ffilt", $ffilt, "Apply SSNR filter to reconstruction (FFILT)" );
		$this->addParam( "fbfact", $fbfact, "Correct B-factor in reconstruction (FBFACT)" );
		$this->addParam( "psi", $psi, "Psi" );
		$this->addParam( "theta", $theta, "Theta" );
		$this->addParam( "phi", $phi, "Phi" );
		$this->addParam( "x", $x, "X" );
		$this->addParam( "y", $y, "Y" );
		$this->addParam( "dstep", $dstep, "Camera physical pixel size in micron" );
		$this->addParam( "fmatch", $fmatch, "save projection match images" );
		// fsearch depends on whether particle params was prepared from results of another refinement run.
		$this->addParam( "fsearch", $fsearch, "Do global brute force search" );
		
		// disable any general params that do not apply to this method
		$this->hideParam("outerAlignRadius");
		$this->hideParam("innerAlignRadius");
		$this->hideParam("angSampRate");
		$this->hideParam("filterEstimated");
		$this->hideParam("filterResolution");
		$this->hideParam("filterComputed");
		$this->hideParam("filterConstant");
		
		// add parameter requirements
		$this->addValidation( "outerMaskRadius", "req" );	
		$this->addValidation( "mw", "req" );	
	}	
}

?>
