<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";

class RunParametersForm extends BasicForm

{
	function __construct( $runname='', $outdir='', $description='', $showDesc=True ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "runparams" );
				
		$params->addParam( "runname", $runname, "Run name" );
		$params->addParam( "outdir", $outdir, "Output directory" );
		$params->addParam( "description", $description, "Description" );
		
		// Add Validations
		$params->addValidation( "description", "noquote" );
		$params->addValidation( "outdir", "req" );
		
		if ( !$showDesc ) {
			$params->hideParam( "description" );
		}
	}
		
	public function generateForm()
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		//$this->params->getPostedValues( $postArray );
		$this->updateFormParams();
		$params = $this->getFormParams();
				
		$html.= openRoundBorder();
		$html.= $params->insertStackedTextField( "runname", 20 );
		$html.= "<br/>\n";
		$html.= $params->insertStackedTextField( "outdir", 56 );
		$html.= "<br/>\n";
		$html.= $params->insertTextArea( "description");
		$html.= closeRoundBorder();
			
		$html.= "<br/>\n";

		return $html;
	}	
	
	// override build Command because runname and outdir are a special case, they
	// are handled in showOrSubmitCommand. We should refactor appion so all methods
	// use this class and remove the special cases.
	public function buildCommand( $postArray )
	{
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = $this->addCommandFlag( $command, "description" );
		
		
		// TODO: We should be adding the rundir here rather than in showOrSubmitCommand
		$outdir		= $params->getParamValue('outdir');
		$runname	= $params->getParamValue('runname');
		if ( $outdir ) {
			// make sure outdir ends with '/' and append run name
			if (substr($outdir,-1,1)!='/') $outdir.='/';
			$rundir = $outdir.$runname;
		}
				
		return $command;
	}
	
}
?>