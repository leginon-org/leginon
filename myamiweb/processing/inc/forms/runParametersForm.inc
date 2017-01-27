<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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
		$params->addValidation( "outdir", "req" );
		
		if ( $showDesc ) {
			//$params->addValidation( "description", "req" ); // This wont work unless we pass the $showDesc param when it should be false.
			$params->addValidation( "description", "noquote" );
		} else { 
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
		$html.= $params->insertStackedTextField( "runname", 30 );
		$html.= "<br/>\n";
		$html.= $params->insertStackedTextField( "outdir", 56 );
		$html.= "<br/>\n";
		$html.= $params->insertTextArea( "description", $cols=3, $rows=50);
		$html.= closeRoundBorder();
			
		$html.= "<br/>\n";

		return $html;
	}	
	
	// override build Command because runname and outdir are a special case, they
	// are added to the command concatenated as "rundir". 
	public function buildCommand( $postArray )
	{
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = $this->addCommandFlag( $command, "description" );
		$command = $this->addCommandFlag( $command, "runname" );
		
		$outdir		= $params->getParamValue('outdir');
		$runname	= $params->getParamValue('runname');
		
		// Create the rundir from outdir and runname
		if ( $outdir ) {
			// make sure outdir ends with '/' and append run name
			if (substr($outdir,-1,1)!='/') $outdir.='/';
			$rundir = $outdir.$runname;
		}
		
		$command = $this->addCommandFlag( $command, "rundir", '',  $rundir);
				
		return $command;
	}
	
}
?>
