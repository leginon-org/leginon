<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";

class AutoMaskForm extends BasicForm

{
	function __construct( $downsample='', $compsizethresh='', $adapthresh='', $blur='',$dilation='', $erosion='') 
	{
		parent::__construct();
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "em_hole_finder" );
				
		$params->addParam( "downsample", $downsample, "Downsample" );
		$params->addParam( "compsizethresh", $compsizethresh, "Component size thresholding" );
		$params->addParam( "adapthresh", $adapthresh, "Adaptive thresholding factor" );
		$params->addParam( "blur", $blur, "Blur window size" );
		$params->addParam( "dilation", $dilation, "Dilation factor" );
		$params->addParam( "erosion", $erosion, "Erosion factor" );
		
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "
	    <br />
	    <H4>Optional Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "downsample", $fieldSize );
		$html.= $params->insertTextField( "compsizethresh", $fieldSize );
		$html.= $params->insertTextField( "adapthresh", $fieldSize );
		$html.= $params->insertTextField( "blur", $fieldSize );
		$html.= $params->insertTextField( "dilation", $fieldSize );
		$html.= $params->insertTextField( "erosion", $fieldSize );
		
		return $html;
	}	
	
}
?>
