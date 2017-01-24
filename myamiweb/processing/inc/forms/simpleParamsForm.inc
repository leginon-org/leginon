<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";

class SimpleParamsForm extends BasicForm

{
	function __construct( $clip='', $bin='', $numpart='', $no_center='',$ring2='', $ncls='',
		$minp='', $nvars='', $mask='', $lp='', $hp='', $froms='', $tos='', $maxits='',
		$mw='', $frac='', $amsklp='', $edge='', $trs='') 
	{
		parent::__construct();
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "simple" );
				
		$params->addParam( "clip", $clip, "unbinned clip diameter" );
		$params->addParam( "bin", $bin, "particle binning" );
		$params->addParam( "numpart", $numpart, "number of particles" );
		$params->addParam( "no_center", $no_center, "DO NOT Center Stack" );
		$params->addParam( "ring2", $ring2, "ring2" );
		$params->addParam( "ncls", $ncls, "number of classes" );
		$params->addParam( "minp", $minp, "minimum PPC" );
		$params->addParam( "nvars", $nvars, "num Eigenvectors" );
		$params->addParam( "mask", $mask, "mask radius" );
		$params->addParam( "lp", $lp, "low-pass" );
		$params->addParam( "hp", $hp, "high-pass" );
		$params->addParam( "froms", $froms, "starting states" );
		$params->addParam( "tos", $tos, "ending states" );
		$params->addParam( "maxits", $maxits, "maximum refinement rounds" );
		$params->addParam( "mw", $mw, "molecular weight" );
		$params->addParam( "frac", $frac, "included fraction" );
		$params->addParam( "amsklp", $amsklp, "auto-masking low-pass" );
		$params->addParam( "edge", $edge, "edge" );
		$params->addParam( "trs", $trs, "translational search" );
		
		// Validations
		$params->addValidation( "numpart", "req" );
	}
		
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 7;
		
		$html .= "
	    <br />
	    <H4>Limiting Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "clip", $fieldSize );
		$html.= $params->insertTextField( "bin", $fieldSize );
		$html.= $params->insertTextField( "numpart", $fieldSize );

		$html .= "
	    <br />
	    <H4>Pre-processing Parameters</H4>
	    <hr />";
		
		$html.= $params->insertCheckboxField( "no_center");
		
		$html .= "
	    <br />
	    <H4>SIMPLE Cluster Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "ring2", $fieldSize );
		$html.= $params->insertTextField( "ncls", $fieldSize );
		$html.= $params->insertTextField( "minp", $fieldSize );
		$html.= $params->insertTextField( "nvars", $fieldSize );
		$html.= $params->insertTextField( "mask", $fieldSize );
		
		$html .= "
	    <br />
	    <H4>SIMPLE Origami Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "lp", $fieldSize );
		$html.= $params->insertTextField( "hp", $fieldSize );
		$html.= $params->insertTextField( "froms", $fieldSize );
		$html.= $params->insertTextField( "tos", $fieldSize );
		$html.= $params->insertTextField( "maxits", $fieldSize );
		$html.= $params->insertTextField( "mw", $fieldSize );
		$html.= $params->insertTextField( "frac", $fieldSize );
		$html.= $params->insertTextField( "amsklp", $fieldSize );
		$html.= $params->insertTextField( "edge", $fieldSize );
		$html.= $params->insertTextField( "trs", $fieldSize );
		
		return $html;
	}	
	
}
?>
