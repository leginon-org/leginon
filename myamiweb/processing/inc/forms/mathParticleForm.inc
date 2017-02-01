<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------


require_once "basicParticleForm.inc";
require_once "particleTable.inc";

class MathParticleForm extends BasicParticleForm
{

	function __construct( $expId, $errorHTML='', $infoHTML='' ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML );	
		$this->mathTable = new MathParticleTable();
		$this->mathAdvancedTable = new MathParticleAdvancedTable(
			$peaktype='centerofmass' );
	}

	public function generateParticleTable() {
		// put Math ParticleTable at front
		$html .= $this->mathTable->generateForm();
	
		$html .= parent::generateParticleTable();
	
		return $html;
	}

	public function generateAdvancedTableRight() {
		// Add the Advanced Particle Loop Form
		$html .= $this->mathAdvancedTable->generateForm();
		return $html;
	}

	// Override the validate function so that we can verify the ParticleTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$msg .= $this->mathTable->validate( $postArray );
		
		return $msg;
	}

	// Override buildCommand so that we can call it from ParticleForm
	public function buildCommand( $postArray )
	{	
		// parent command includes SimpleParticleTable values
		$command = parent::buildCommand( $postArray );
		
		// add params from Appion Loop form
		$command .= $this->mathTable->buildCommand( $postArray );
		$command .= $this->mathAdvancedTable->buildCommand( $postArray );
		
		return $command;		
	}
}

?>
