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


class RelionRefineForm extends BasicRefineForm 
{
	// Return an instance of the FormParameters that correspond to this method.
	// In this case, the parameter class is defined at the end of this file.
	public function createFormParams() { return new RelionParams(); }
	
	protected function setPublications()
	{
		// This array of keys should include any publications that need to be cited for this refine method
		// and correspond to the array keys found in publicationList.inc.
		$this->pubKeyList = array("relion");
	}
	
	// This function returns the html code that defines the GUI layout of this method's parameters. 
	// It is called from the BasicRefineForm class which places this html in an appropriate location on the screen.
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// This help section key corresponds to the section in help.js that defines
		// help messages for this piece of the GUI.
		$params->setHelpSection( "relion" );		
		
		$fieldSize = 3;
		
		$html .= "<b>Basic Relion Options</b><br/>\n";
		$html .= $params->insertCheckboxField( "ctf" );
		$html .= $params->insertCheckboxField( "ctf_corrected_ref" );		
		$html .= $params->insertTextField( "ini_high", $fieldSize, "(&Aring;ngstroms)" );
		$html .= "<br/>\n";
		
		
		$html .= "<b>Advanced Relion Options</b><br/>\n";
		$html .= $params->insertCheckboxField( "ctf_intact_first_peak" );
		$html .= $params->insertTextField( "offset_range", $fieldSize, "(pix)" );
		$html .= $params->insertTextField( "offset_step", $fieldSize, "(pix)" );
		$healpixOptions = array(30, 15, 7.5, 3.5, 1.8, 0.9, 0.5, 0.2, 0.1);
		$healpixOptions = array_combine( $healpixOptions, $healpixOptions ); //need a dict with key and value set to degrees
		$html .= $params->insertSelectField( "healpix_order", $healpixOptions, "(degrees)" );
		$html .= $params->insertSelectField( "auto_local_healpix_order", $healpixOptions, "(degrees)" );
		$html .= "<br/>\n";	
		
		return $html;
	}
	
	// override this function for importing previous run params to the form
	// since relion does not allow different values for different iterations,
	// only the first iteration needs to be added to the form param.
	// @override
	protected function addImportedRefineIter( $paramSet, $iter ) 
	{
		$paramSet->addIterationToValue( "ctf", $iter['ctf'] );
		$paramSet->addIterationToValue( "ctf_intact_first_peak", $iter['ctf_intact_first_peak'] );
		$paramSet->addIterationToValue( "ctf_corrected_ref", $iter['ctf_corrected_ref'] );
		$paramSet->addIterationToValue( "ini_high", $iter['ini_high'] );
		$paramSet->addIterationToValue( "healpix_order", $iter['healpix_order'] );
		$paramSet->addIterationToValue( "auto_local_healpix_order", $iter['auto_local_healpix_order'] );
		$paramSet->addIterationToValue( "offset_range", $iter['offset_range'] );
		$paramSet->addIterationToValue( "offset_step", $iter['offset_step'] );
	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		$stack = $this->getStackInfo();
		$box = $stack['boxsize'];
		$apix = $stack['apix'];
		$sym = $this->getSymmetry();
		
		// There are different default values for icosohedral symmetries
		if ( stripos($sym, "icos") ) {
			$healpix_order = 3.7;
			$auto_local_healpix_order = 0.9;
		} else {
			$healpix_order = 7.5;
			$auto_local_healpix_order = 1.8;
		}
		
		$radPix = ($box/2)-2;
		$radAng = round($radPix * $apix);
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $radAng;
	      if (obj.symmetry) obj.symmetry.value = '$sym';
	      if (obj.ctf) obj.ctf.checked = true;
	      if (obj.ctf_intact_first_peak) obj.ctf_intact_first_peak.checked = false;
	      if (obj.ctf_corrected_ref) obj.ctf_corrected_ref.checked = false;
	      if (obj.ini_high) obj.ini_high.value = '60';
	      if (obj.healpix_order) obj.healpix_order.value = $healpix_order;
	      if (obj.auto_local_healpix_order) obj.auto_local_healpix_order.value = $auto_local_healpix_order;
	      if (obj.offset_range) obj.offset_range.value = '5';
	      if (obj.offset_step ) obj.offset_step.value = '1';

	      return;
	    }
	  </script>\n";
		return $javafunc;
	}	

	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		
		// endIter is always 1 for relion
		$command .= " --endIter=1 ";
		
		return $command;
	}
} // End of Refine Form class

// extend the RefineFormParameters class to add
// method specific parameter default values. 
class RelionParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$ctf='', $ctf_intact_first_peak='', $ctf_corrected_ref='', $ini_high='', $healpix_order='', 
							$auto_local_healpix_order='', $offset_range='', $offset_step='' ) 
	{
		// Call the parent constructor to create the general refine params. Any of these may be hidden with a subsequent 
		// call to hideParam().
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
									
		$this->addParam( "ctf", $ctf, "Do CTF-correction " );
		$this->addParam( "ctf_intact_first_peak", $ctf_intact_first_peak, "Ignore CTFs until first peak " );		
		$this->addParam( "ctf_corrected_ref", $ctf_corrected_ref, "Reference model is CTF-corrected " );		
		$this->addParam( "ini_high", $ini_high, "Initial low-pass filter " );
		$this->addParam( "healpix_order", $healpix_order, "Angular sampling interval " );
		$this->addParam( "auto_local_healpix_order", $auto_local_healpix_order, "Local searches from auto-sampling " );
		$this->addParam( "offset_range", $offset_range, "Offset search range " );
		$this->addParam( "offset_step", $offset_step, "Offset search step " );
		
		// disable any general params that do not apply to this method
		$this->hideParam("innerMaskRadius");		
		$this->hideParam("outerAlignRadius");		
		$this->hideParam("innerAlignRadius");		
		$this->hideParam("endIter");		
		$this->hideParam("angSampRate");		
		$this->hideParam("percentDiscard");		
		$this->hideParam("filterEstimated");		
		$this->hideParam("filterResolution");		
		$this->hideParam("filterComputed");		
		$this->hideParam("filterConstant");		
	}
}

?>
