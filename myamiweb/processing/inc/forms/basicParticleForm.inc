<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------


require_once "basicLoopForm.inc";
require_once "particleTable.inc";

class BasicParticleForm extends BasicLoopForm
{

	function __construct( $expId, $errorHTML='', $infoHTML='' ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML );
		$this->particleTable = new SimpleParticleTable();
		$this->pDiameterTable = new ParticleDiameterTable();
		$this->imageContrastTable = new ImageContrastTable();
		$this->showfilters=true;
		// You can change the default of the parameters for the imbeded table in the child functions.

	}

	// Thie overwrite the same function in BasicLoopForm to divide the
	// form table in three.	
	public function generateAdditionalFormRight() {
		$formRightHeader = $this->generateAdditionalFormRightHeader();		
		$formRightBody = $this->generateAdditionalFormRightBody();		
		if ( $formRightHeader ) {
			$html .= "<tr><td valign='top'>\n";
			$html .= $formRightHeader;
			$html .= "</td>\n";
			$html .= "</tr>\n";
		}
		if ( $formRightBody ) {
			$html .= "<tr><td valign='top'>\n";
			$html .= $formRightBody;
			$html .= "</td>\n";
			$html .= "</tr>\n";
		}
		return $html;
	}

	public function generateParticleTable() {
		// Add the Particle Loop Form
		//$particleTable = SimpleParticleTable();

		$this->particleTable->setShowFilters($this->showfilters);
		$html .= $this->particleTable->generateForm();
		$html .= $this->imageContrastTable->generateForm();

		return $html;
	}

	// This html will be displayed on the first section on right hand side of the form
	// overwrite this to return false if don't want Diameter to show
	public function generateAdditionalFormRightHeader() {
		// Add the Particle Parameter Table Form
		$html .= $this->pDiameterTable->generateForm();
		return $html;
	}
		
	// This html will be displayed on the second section on right hand side of the form
	// overwrite this to return false if don't want ParticleTable to show
	public function generateAdditionalFormRightBody() {
		// Add the Particle Parameter Table Form
		$html .= $this->generateParticleTable();
		return $html;
	}

	// Override the validate function so that we can verify the ParticleTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$msg .= $this->pDiameterTable->validate( $postArray );

		$msg .= $this->particleTable->validate( $postArray );
		$msg .= $this->imageContrastTable->validate( $postArray );
		
		return $msg;
	}

	// Override buildCommand so that we can call it from ParticleForm
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		// add params from forms
		$command .= $this->pDiameterTable->buildCommand( $postArray );
		$command .= $this->particleTable->buildCommand( $postArray );
		$command .= $this->imageContrastTable->buildCommand( $postArray );
		
		return $command;		
	}
}

?>
