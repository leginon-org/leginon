<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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
		$particleTable = new SimpleParticleTable();
		
		$html .= $particleTable->generateForm();
	
		return $html;
	}

	// This html will be displayed on the first section on right hand side of the form
	// overwrite this to return false if don't want Diameter to show
	public function generateAdditionalFormRightHeader() {
		// Add the Particle Parameter Table Form
		$pDiameterTable = new ParticleDiameterTable();
		$html .= $pDiameterTable->generateForm();
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
		
		$pDiameterTable = new ParticleDiameterTable();
		$msg .= $pDiameterTable->validate( $postArray );

		$particleTable = new SimpleParticleTable();
		$msg .= $particleTable->validate( $postArray );
		
		return $msg;
	}

	// Override buildCommand so that we can call it from ParticleForm
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		// add params from Appion Loop form
		$pDiameterTable = new ParticleDiameterTable();
		$particleTable = new SimpleParticleTable();
		$command .= $pDiameterTable->buildCommand( $postArray );
		$command .= $particleTable->buildCommand( $postArray );
		
		return $command;		
	}
}

?>
