<?php
require_once "formValidator.php";
require_once "formGenerator.inc";

// examples of use are found in runParametersForm.inc, stackPrepForm.inc.
// an example of how to extend this class is the RefineFormParameters class found in basicRefineForm.inc.

class FormParameters
{
	private $params; //array of parameters
	private $helpSection; // corresponds to array key in help.js associated with this form
	
	function __construct( $id='', $label='', $helpSection='' ) 
	{
		$this->id 			= $id;
		$this->label 		= $label;
		$this->helpSection 	= $helpSection;
		
		$this->formLib = new FormGeneratorLib();
	}
	
	public function setHelpSection( $helpSection ) 
	{
		$this->helpSection = $helpSection;
	}
	
	public function getHelpSection() 
	{
		return $this->helpSection;
	}
	
	// add a parameter to the list of parameters. This may be used in the constructor.
	// example usage: 	$this->addParam( "numIters", 10, "number of iterations" );
	//
	// params are a name indexed array of parameters, which are themselves arrays 
	// containing fields for name, value, label, and enable.	
	final public function addParam( $name, $defaultValue='', $label='', $enable='', $hidden=false )
	{
		if ( !empty( $name ) ) {
			$this->params[$name] = array( "name"=>$name, "value"=>$defaultValue, "label"=>$label, "enable"=>$enable, "hidden"=>$hidden, "default"=>$defaultValue );
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
	
	final public function setParamDefault( $name, $value ) 
	{
		$this->params[$name]["default"] = $value;
	}
	
	final public function getParamDefault( $name ) 
	{
		return $this->params[$name]["default"];
	}
	
	final public function setParamLabel( $name, $label ) 
	{
		$this->params[$name]["label"] = $label;
	}
	
	final public function getParamLabel( $name ) 
	{
		return $this->params[$name]["label"];
	}
	
	// Returns True if Hidden, otherwise False
	final public function isHidden( $name ) 
	{
		return $this->params[$name]["hidden"];
	}
	
	// returns the parameter array
	final public function getParamArray()
	{
		return $this->params;
	}
		
	// extending classes should use this disable function in the constructor
	// to disable (grey out) params.
	final public function disableParam( $name ) 
	{
		$this->params[$name]["enable"] = 'DISABLED';
	}
	
	final public function disableAllParams()
	{
		foreach ( $this->params as $name=>$param ) {
			$this->disableParam( $name );
		}
	}
	
	// extending classes should use this function in the constructor
	// to completely hide the parameter.
	final public function hideParam( $name ) 
	{
		$this->params[$name]["hidden"] = true;
	}
	
	
	// TODO: rename to updateParamValues for more general purpose???
	final public function getPostedValues($postArray)
	{
		// Forms with no parameters defined will not have valid params
		if ( $this->params ) {
			foreach ( $this->params as $key=>$param ) {
				// TODO: fix this so we don't get NULL values but keep empty string and 0 and 0.0...
				if ( !empty( $postArray[$param["name"]] ) || $postArray[$param["name"]] === '0' ) {
					$value = $postArray[$param["name"]];
		
					// if the value has spaces and has not yet ben quoted, 
					// put quotes around it to aid parsing later
					$value = trim($value);
					if ( strpos($value, " ") ) {
						if ( !preg_match('/"([^"]*)"/', $value) ) {
							$value = '"'.$value.'"';
						}
					}
		
					$this->params[$key]["value"] = $value;
				} else if ( $postArray['process'] && empty( $postArray[$param["name"]] ) ) {
					// TODO: Checking if the form has been submitted is very ugly here, 
					// try passing in a value from to parent form (runAppionLoop.php) to
					// decide if we should check for empty checkboxes...
					$this->params[$key]["value"] = '';
				}
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
		 * Exclude (must not set if the other exist: addValidation("variableName", "exclude="other_variableName","error message");
	*/
	public function addValidation( $name, $requirement, $error_message=NULL) 
	{
		$this->validations[] = array( "name"=>$name, "req"=>$requirement, "msg"=>$error_message );
	}
	
	// override the validate function for error checking.
	public function validate() 
	{
		// If no validations have been added, just return
		if ( empty($this->validations) ) {
			return;
		}
		
		$validator = new formValidator();

		foreach ( $this->validations as $validate ) {
			$name 			= $validate["name"];
			$requirement 	= $validate["req"];
			$msg 	= $validate["msg"];
			// if this parameter has been hidden, skip it.
			if ( !$this->params[$name]['hidden'] ) {
				// need to get other variable value in exclude validation
				// syntax is 'exclude=other_variable'
				if ( strrpos($requirement,'exclude') !== false ) {
					$bits = explode('=',$requirement);
					if ( count($bits) > 1 ) {
						$other_variable = $bits[1];
						$other_value = $this->getParamValue($other_variable);
						$requirement .= ','.$other_value;
					}
				}
				$validator->addValidation( $name, $this->getParamValue($name), $requirement, $msg );
			}
		}

		$validator->runValidation();
		$errorArray = $validator->getErrorMessage();

		foreach ( $errorArray as $name => $error ) {
			$errorMsg .= "<b>Error: </b><i> ".$this->params[$name]['label']."</i> - $error <br />\n";
		}
		
		return $errorMsg;
	}
	
	// -----------------------------------------------
	// Begin html element funtions
	// -----------------------------------------------
	private function setHelpKey( $name, $helpkey='' ) 
	{
		// if the help key is empty, and the helpSection is set, prepend the help section 
		// to the name of the parameter. If the helpSection is not set, just use the name.
		if (empty( $helpkey )) {
			$helpkey = ( !empty($this->helpSection) ) ? $this->helpSection.".".$name : $name;
		}
		
		return $helpkey;
	}
	
	public function insertTextArea( $name, $rows=3, $cols=65, $note='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$html = $this->formLib->insertTextArea( $this->params[$name]['name'], 
													$this->params[$name]['label'], 
													$this->params[$name]['value'], 
													$rows, 
													$cols, 
													$this->params[$name]['enable'], 
													$note,
													$helpkey );
		}
		
		return $html;
	}
	
	public function insertTextField( $name, $size=20, $note='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$html = $this->formLib->insertTextField( $this->params[$name]['name'], 
													$this->params[$name]['label'], 
													$this->params[$name]['value'], 
													$size, 
													$this->params[$name]['enable'], 
													$note,
													$helpkey );
		}
		
		return $html;
	}
	
	public function insertTextFieldInRow( $name, $size=20, $note='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );					
			$html = $this->formLib->insertTextFieldInRow( $this->params[$name]['name'], 
													$this->params[$name]['label'], 
													$this->params[$name]['value'], 
													$size, 
													$this->params[$name]['enable'], 
													$note,
													$helpkey );
		}
		
		return $html;
	}
	
	public function insertStackedTextField( $name, $size=20, $note='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$html = $this->formLib->insertStackedTextField( $this->params[$name]['name'], 
															$this->params[$name]['label'], 
															$this->params[$name]['value'], 
															$size, 
															$this->params[$name]['enable'], 
															$note,
															$helpkey );
		}
			
		return $html;
	}
	
	// This control is used for setting "flags" that appear in the form
	// '--name' in the generated command. We use the value 'on' to indicate
	// that the checkbox has been checked by the user. 
	// TODO: May want to clean up the hard coded 'on' value as it is referenced
	// in basicForm.inc as well to indicate that a flag should be added to a command. 
	public function insertCheckboxField( $name, $note='', $helpkey='', $onchange=''  )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$checked = ( $this->params[$name]['value'] == "on" ) ? "CHECKED" : "";
			$html = $this->formLib->insertCheckboxField( $this->params[$name]['name'], 
														$this->params[$name]['label'], 
														"on", /*sets $this->params[$name]['value'] to 'on' if checked by user*/
														$checked, 
														$this->params[$name]['enable'], 
														$note,
														$helpkey,
														$onchange );
		}

		return $html;
	}		

	public function insertRadioField( $name, $value, $label, $note='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$checked = ( $this->params[$name]['value'] == $value ) ? "CHECKED" : "";
			$html = $this->formLib->insertRadioField( $this->params[$name]['name'], 
														$label, 
														$value,
														$checked, 
														$this->params[$name]['enable'], 
														$note,
														$helpkey );
		}

		return $html;
	}		
	
	public function insertSubmitField( $name, $value, $label='', $helpkey='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );			
			$html = $this->formLib->insertSubmitField( $this->params[$name]['name'], 
														$label, 
														$value,
														$helpkey );
		}

		return $html;
	}		
	
	// $options is an array of options for the selection box. 
	// Options must be a dictionary, to allow a more descriptive string to be shown to the user for each option. 
	// Use onchange to pass a javascript function name 
	public function insertSelectField( $name, $options, $note='', $helpkey='', $onchange='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );	
			$html = $this->formLib->insertSelectField( $this->params[$name]['name'], 
														$this->params[$name]['label'], 
														$this->params[$name]['value'],
														$options, 
														$this->params[$name]['enable'], 
														$note,
														$helpkey,
														$onchange );
		}

		return $html;
	}		
	
	// $options is an array of options for the selection box. 
	// Options may be a dictionary, to allow a more descriptive string to be shown to the user for each option.  
	// Use onchange to pass a javascript function name
	public function insertStackedSelectField( $name, $options, $note='', $helpkey='', $onchange='' )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$helpkey = $this->setHelpKey( $name, $helpkey );	
			$html = $this->formLib->insertStackedSelectField( $this->params[$name]['name'], 
														$this->params[$name]['label'], 
														$this->params[$name]['value'],
														$options, 
														$this->params[$name]['enable'], 
														$note,
														$helpkey,
														$onchange );
		}

		return $html;
	}	

	// Generates <input type='HIDDEN' NAME='$name' value='$value'>\n";
	public function insertHiddenField( $name )
	{
		// if the parameter has been "hidden" just return an empty string.
		if ( $this->params[$name]['hidden'] ) {
			$html = "";
		} else {
			$html = $this->formLib->insertHiddenField( $this->params[$name]['name'], 
														$this->params[$name]['value'] );
		}

		return $html;
	}
	
}

?>
