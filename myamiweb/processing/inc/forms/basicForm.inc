<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "../inc/formParameters.inc";


class BasicForm
{
	protected $defaultParamSets; 	// an array of parameter sets of type RefineFormParameters used for populating forms
	protected $formParams; 			// the current user selected or modified parameter set
	
	function __construct() 
	{
		$this->formParams = $this->createFormParams();
	}	
	
	function __destruct() 
	{
		unset( $this->formParams );
		unset( $this->defaultParamSets );
	}
		
	// Extending classes should override this function to return the appropriate
	// class of form parameters if it has also extended the FormParameters class.
	// This createFormParams() function should always be used instead of 
	// directly creating an instance of FormParameters.
	// GOOD: $formParams = $this->createFormParams();
	// BAD:  $formParams = new FormParameters();
	public function createFormParams( $id='', $label='' ) 
	{ 
		return new FormParameters( $id, $label ); 
	}
			
	// adds a set of default values to the "Import Parameters"
	// drop dowm list.
	final protected function addDefaultParams( $newSet )
	{
		$this->defaultParamSets[$newSet->id] = $newSet;
	}
	
	// points the form parameters to the correct set of default
	// values based on the users selection.
	// Takes the default set Id, which corresponds to a set available
	// in the "Import Parameters" drop down list.	
	protected function updateFormParams( $defaultSetId='' )
	{
		if ( isset( $this->defaultParamSets[$defaultSetId] ) ) {
			// the user just selected an existing set of params to import
			$this->formParams = $this->defaultParamSets[$defaultSetId];			
		} else {
			// the form may be refreshing after posting an error, make sure to get any previous values from the POST array
			$this->formParams->getPostedValues($_POST);
		}
	}
	
	// returns an array of all form parameters
	// with the currently set values
	final protected function &getFormParams()
	{
		return $this->formParams;
	}
	
	// returns an array of all form parameters
	// with the currently set values
	final protected function getDefaultParamSets()
	{
		return $this->defaultParamSets;
	}

	// use this function in the form constructor
	// to completely hide the parameter in the form.	
	public function hideParam( $name )
	{
		$this->formParams->hideParam( $name );
	}
		
	public function disableAllParams()
	{
		$this->formParams->disableAllParams();
	}
	
	public function generateForm() {}
	
	public function generateReport( $title="", $width=650 )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->updateFormParams();
		$params = $this->getFormParams();		
		$paramArray = $params->getParamArray();

		// Add a rounded border table
		$html.= "<table border='0' cellpadding='2' cellspacing='2' >\n";
		//$html.= "<tr><td>\n";
		//$html.= openRoundBorder();
		//$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";
		
		// Add title
		if ( $title ) {
			$html.= "<tr>\n";
			$html.= "<td colspan='2'>\n";
			$html.= "<h4>".$title."</h4>\n";
			$html.= "</td>\n";
			$html.= "</tr>\n";
		}
		
		// Add each parameter's label and value
		foreach ( $paramArray as $key=>$param ) {
			$html.= "<tr><td><b>".$param['label'].":</b></td><td>".$param['value']."</td></tr>\n";
			// Since just displaying the values does not add them to the post array, 
			// post them here so we can still add them to a command later 
			$html.= "<input type='hidden' NAME='".$param['name']."' value='".$param['value']."'>\n";
		}

		// Close the table
		$html.= "</table>\n";
		//$html.= closeRoundBorder();
		//$html.= "</td></tr>\n";
		//$html.= "</table>\n";
		
		$html.= "<br/>\n";

		return $html;
	}
	
	
	// A generic default implementation that will add
	// a flag to a command string for every parameter 
	// defined by the form in format --<name>=<value>
	public function buildCommand( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );
		$paramArray = $this->formParams->getParamArray();
				
		foreach ( $paramArray as $key=>$param ) {
			$command = $this->addCommandFlag( $command, $param['name'] );
		}
		
		return $command;
	}
	
	// Appends a new command flag to a command string
	// If value is not passed, the param value is looked up.
	// If $paramName is not passed, it is assumed to be the same 
	// as the flag name.
	// If the value is an empty string, it is not added to the command.
	// Returns the new command string.
	function addCommandFlag( $command, $flagName, $paramName='', $value='' )
	{
		if ( $paramName == '' ) {
			$paramName = $flagName;
		}
		if ( $value === '' ) {
			$value = $this->formParams->getParamValue( $paramName );
		}
		if ( $value !== '' ) {
			// if the value is 'on' it is just a flag, with no value specified
			if ( $value == 'on') {
				$command .= "--".$flagName." ";
			} else {
				$command .= "--".$flagName."=".$value." ";
			}
		}
		
		return $command;
	}
	
	// remove a specific flag from a command string
	function removeCommandFlag( $command, $flagName, $paramName='', $value='' )
	{
		if ( $paramName == '' ) {
			$paramName = $flagName;
		}
		if ( $value === '' ) {
			$value = $this->formParams->getParamValue( $paramName );
		}
		if ( $value !== '' ) {
			// if the value is 'on' it is just a flag, with no value specified
			if ( $value == 'on') $flagString = "--".$flagName;
			else $flagString = "--".$flagName."=".$value." ";
			$command = str_replace( $flagString,"", $command );
		}
		
		return $command;
	}
	
	public function validate( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );
		$msg = $this->formParams->validate();
		
		return $msg;
	}
}

?>
