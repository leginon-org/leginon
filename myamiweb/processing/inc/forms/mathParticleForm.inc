<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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
	}

	public function generateParticleTable() {
		// put Math ParticleTable at front
		$mathTable = new MathParticleTable();
		$html .= $mathTable->generateForm();
	
		$html .= parent::generateParticleTable();
	
		return $html;
	}

	public function generateAdvancedTableRight() {
		// Add the Advanced Particle Loop Form
		$particleAdvancedTable = new MathParticleAdvancedTable(
	$peaktype='centerofmass' );
		$html .= $particleAdvancedTable->generateForm();
		return $html;
	}

	// Override the validate function so that we can verify the ParticleTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$particleTable = new MathParticleTable();
		$msg .= $particleTable->validate( $postArray );
		
		return $msg;
	}

	// Override buildCommand so that we can call it from ParticleForm
	public function buildCommand( $postArray )
	{	
		// parent command includes SimpleParticleTable values
		$command = parent::buildCommand( $postArray );
		
		// add params from Appion Loop form
		$particleTable = new MathParticleTable();
		$advancedTable = new MathParticleAdvancedTable();
		$command .= $particleTable->buildCommand( $postArray );
		$command .= $advancedTable->buildCommand( $postArray );
		
		return $command;		
	}
}

?>
