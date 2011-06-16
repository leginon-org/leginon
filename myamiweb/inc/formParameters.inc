<?php
require_once "formValidator.php";
require_once "formGenerator.inc";

// examples of use are found in runParametersForm.inc, stackPrepForm.inc.
// an example of how to extend this class is the RefineFormParameters class found in basicRefineForm.inc.

class FormParameters
{
	function __construct() 
	{
		$this->formLib = new FormGeneratorLib();
	}

	// add a parameter to the list of parameters. This may be used in the constructor.
	// example usage: 	$this->addParam( "numIters", 10, "number of iterations" );
	//
	// params are a name indexed array of parameters, which are themselves arrays 
	// containing fields for name, value, label, and enable.	
	final public function addParam( $name, $defaultValue='', $label='', $enable='', $hidden=false )
	{
		if ( !empty( $name ) ) {
			$this->params[$name] = array( "name"=>$name, "value"=>$defaultValue, "label"=>$label, "enable"=>$enable, "hidden"=>$hidden );
		}
	}
	
	final public function setParamValue( $name, $value ) 
	{
		$this->params[$name]["value"] = $value;
	}
	
	final public function getParamValue( $name ) 
	{
		return $this->params[$name]["value"];
	}
	
	final public function setParamLabel( $name, $label ) 
	{
		$this->params[$name]["label"] = $label;
	}
	
	// returns the parameter array
	final public function getParamArray()
	{
		return $this->params;
	}
		
	// extending classes should use this disable function in the constructor
	// to disable (grey out) params.
	final protected function disableParam( $name ) 
	{
		$this->params[$name]["enable"] = 'DISABLED';
	}
	
	// extending classes should use this function in the constructor
	// to completely hide the parameter.
	final protected function hideParam( $name ) 
	{
		$this->params[$name]["hidden"] = true;
	}
	
	// TODO: rename to updateParamValues ???
	final public function getPostedValues($postArray)
	{
		foreach ( $this->params as $key=>$param ) {
			if ( !empty( $postArray[$param["name"]] ) ) {
				$this->params[$key]["value"] = $postArray[$param["name"]];
			}
		}
	}
	
	// available validations, check formValidator.php for changes:
	/*
		 * required : 					addValidation("variableName", "req");
		 * MaxLengh : 					addValidation("variableName", "maxlen=10");
		 * MinLengh : 					addValidation("variableName", "mixlen=3");
		 * Email	: 					addValidation("variableName", "email");
		 * Numeric	: 					addValidation("variableName", "num");
		 * Alphabetic : 				addValidation("variableName", "alpha");
		 * Alphabetic and spaces : 		addValidation("variableName", "alpha_s");
		 * Alpha-numeric and spaces: 	addValidation("variableName", "alnum_s");
		 * Float: 						addValidation("variableName", "float");
		 * absolute path: path_exist: 	addValidation("variableName", "abs_path");
		 * path existence : 			addValidation("variableName", "path_exist");
		 * folder permission : 			addValidation("variableName", "folder_permission");
		 * file existence : 			addValidation("variableName", "file_exist");
		 * Float w/fixed decimal space: addValidation("variableName", "float_d=2");
	*/
	public function addValidation( $name, $requirement) 
	{
		$this->validations[] = array( "name"=>$name, "req"=>$requirement );
	}
	
	// override the validate function for error checking.
	public function validate() 
	{
		$validator = new formValidator();

		foreach ( $this->validations as $validate ) {
			$name 			= $validate["name"];
			$requirement 	= $validate["req"];
			
			$validator->addValidation( $this->params[$name]['name'], $this->params[$name]['value'], $requirement );
		}

		$validator->runValidation();
		$errorArray = $validator->getErrorMessage();
		
		foreach ( $errorArray as $name => $error ) {
			$errorMsg .= "<b>Error: </b><i> ".$this->params[$name]['label']."</i> - $error <br />\n";
		}
		
		return $errorMsg;
	}
	
	public function insertTextField( $name, $size=20, $note='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$html = $this->formLib->insertTextField( $this->params[$name]['name'], 
													$this->params[$name]['label'], 
													$this->params[$name]['value'], 
													$size, 
													$this->params[$name]['enable'], 
													$note );
		}
		
		return $html;
	}
	
	public function insertStackedTextField( $name, $size=20, $note='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$html = $this->formLib->insertStackedTextField( $this->params[$name]['name'], 
															$this->params[$name]['label'], 
															$this->params[$name]['value'], 
															$size, 
															$this->params[$name]['enable'], 
															$note );
		}
			
		return $html;
	}
	
	public function insertCheckboxField( $name, $note='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$html = $this->formLib->insertCheckboxField( $this->params[$name]['name'], 
														$this->params[$name]['label'], 
														$this->params[$name]['value'], 
														$this->params[$name]['enable'], 
														$note );
		}

		return $html;
	}		

	public function insertRadioField( $name, $value, $label, $note='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$checked = ( $this->params[$name]['value'] == $value ) ? "CHECKED" : "";
			$html = $this->formLib->insertRadioField( $this->params[$name]['name'], 
														$label, 
														$value,
														$checked, 
														$this->params[$name]['enable'], 
														$note );
		}

		return $html;
	}		
}

?>