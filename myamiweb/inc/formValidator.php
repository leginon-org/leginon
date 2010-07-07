<?php
/**
 * 
 * @author erichou
 * 
 * The class that does user input validations
 * 
 * example of how to use it:
 * 
 * $validator = new formValidator();
 * 
 * $validator->addValidation($variableName, $variableValue, "req", "Please fill in this field");
 * 
 * $validator->runValidation();
 * $errMsg = $validator->getErrorMessage();
 * 
 * if( empty($errMsg) )
 * 		print "There is no error";
 * else
 * 		print_r($errMsg);
 *
 * For regular-Expression tester, you can go to : http://www.spaweditor.com/scripts/regex/index.php
 * 
 */

class formValidator{

	var $validateObjs;
	var $errorMessages;
	
	function formValidator(){
		
		$this->validateObjs = array();
		$this->errorMessages = array();
	}
	
	/**
	 * Example of how to use different type of validations as follow
	 * You can change the errorOutputMessage by enter your own message at the end.
	 * 
	 * required : 
	 * 				addValidation("variableName", "variableValue", "req");
	 * 				addValidation("variableName", "variableValue", "req", "Your own error message");
	 * MaxLengh : 
	 * 				addValidation("variableName", "variableValue", "maxlen=10");
	 * 				addValidation("variableName", "variableValue", "maxlen=10", "Your own error message");
	 * MinLengh : 
	 * 				addValidation("variableName", "variableValue", "mixlen=3");
	 * 				addValidation("variableName", "variableValue", "mixlen=3" , "Your own error message");
	 * Email	: 
	 * 				addValidation("variableName", "variableValue", "email");
	 * 				addValidation("variableName", "variableValue", "email", "Your own error message");
	 * 
	 * Numeric	: 
	 * 				addValidation("variableName", "variableValue", "num");
	 * 				addValidation("variableName", "variableValue", "num", "Your own error message");
	 * 
	 * Alphabetic	: 
	 * 				addValidation("variableName", "variableValue", "alpha");
	 * 				addValidation("variableName", "variableValue", "alpha", "Your own error message");
	 * 
	 * Alphabetic and spaces	: 
	 * 				addValidation("variableName", "variableValue", "alpha_s");
	 * 				addValidation("variableName", "variableValue", "alpha_s", "Your own error message");
	 * 
	 * Alpha-numeric and spaces: 
	 * 				addValidation("variableName", "variableValue", "alnum_s");
	 * 				addValidation("variableName", "variableValue", "alnum_s", "Your own error message");
	 * 
	 * Float:
	 * 				addValidation("variableName", "variableValue", "float");
	 * 				addValidation("variableName", "variableValue", "float", "Your own error message");
	 * 
	 * Float with fixed number of decimal:
	 * 				addValidation("variableName", "variableValue", "float_d=2");
	 * 				addValidation("variableName", "variableValue", "float_d=2", "Your own error message");
	 * 
	 * SMTP server validation:
	 * 				addValidation("smtp_server", array( 'host' => 'hostname', 
	 *													'email' => 'email address',
	 *													'auth' => true/false, 
	 *													'username' => 'username',
	 *													'password' => 'password'), "smtp");
	 * 
	 */
	function addValidation($variableName, $variableValue, $validatorType, $errorOutputMessage=NULL){
		
		$validatorObj = new validatorObj();
		
		$validatorObj->setVariableName($variableName);
		$validatorObj->setVariableValue($variableValue);
		$validatorObj->setValidatorType($validatorType);
		$validatorObj->setErrorOutputMessage($errorOutputMessage);
		
		array_push($this->validateObjs, $validatorObj);
	}
	
	function getErrorMessage(){
		return $this->errorMessages;
	}
	
	function getValidateObjes(){
		return $this->validateObjs;
	}
	
	// run this function to start the validation
	function runValidation(){
		
		$result = true;
		
		// loop through each objects
		foreach($this->validateObjs as $validateObj){
			
			// when validate fail, put it in to the error message array.
			if(!$this->validate($validateObj)){
				$result = false;

				$this->errorMessages[$validateObj->getVariableName()] = $validateObj->getErrorOutputMessage();
			}			
		}
		
		return $result;
	}
	
	/*
	 * This function will find out what kinds validation function need to use.
	 */
	function validate($validateObj){
		
		$result = true;

		switch($validateObj->getValidatorType()){
			
			case 'req':{
				$result = $this->validateReq($validateObj->getVariableValue());
				break;
			}
			
			case 'maxlen':{
				$result = $this->validateMaxlen($validateObj->getVariableValue(), $validateObj->getTypeOption());
				break;
			}
			
			case 'minlen':{
				$result = $this->validateMinlen($validateObj->getVariableValue(), $validateObj->getTypeOption());
				break;
			}
			
			case 'email':{
				$result = $this->validateEmail($validateObj->getVariableValue());
				break;
			}
			
			case 'num':{
				$result = $this->validateRegExp($validateObj->getVariableValue(),"/^[0-9]*$/");
				break;							
            }

			case 'alpha':{														
				$result = $this->validateRegExp($validateObj->getVariableValue(),"/^[A-Za-z]*$/");
				break;
			}
			
			case 'alpha_s':{
				$result = $this->validateRegExp($validateObj->getVariableValue(),"/^[A-Za-z ]*$/");
				break;
			}
			
			case 'alnum_s':{
				$result = $this->validateRegExp($validateObj->getVariableValue(), "/^[A-Za-z0-9 ]*$/");
				break;
			}
			
			case 'float':{
				$result = $this->validateRegExp($validateObj->getVariableValue(), "/^\d*\.?\d*$/");
				break;
			}
			
			case 'float_d':{
				$numberOfDecimal = $validateObj->getTypeOption();
				
				$floatRegExp = "/^\d*\.\d{". $numberOfDecimal ."}$/";
				$result = $this->validateRegExp($validateObj->getVariableValue(), $floatRegExp);
				break;
			}
			
			case 'db_connect':{
				
				break;
			}
			
			case 'smtp':{
				$result = $this->validateSMTP($validateObj);
				break;
			}
			
		
		} //end switch

		return $result;
	}
	
	/*
	 * Validate "req" field
	 */
	function validateReq($inputValue){
		$result = true;
      	
		if(!isset($inputValue) || strlen($inputValue) <=0)
			$result = false;
			
		return $result;	
	}
	
	/*
	 * Validate Max length of input value
	 */
	function validateMaxlen($inputValue, $maxLength){
		
		$result = true;
		
		if(isset($inputValue)){
			
			$inputLength = strlen($inputValue);
			
			if($inputLength > $maxLength)				
				$result=false;
		}
		return $result;
	}
	
	/*
	 * Validate Min length of input value
	 */
	function validateMinlen($inputValue, $minLength){
		
		$result = true;
		
		if(isset($inputValue) ){
			
			$inputLength = strlen($inputValue);
			
			if($inputLength < $minLength)
				$result=false;
		}
		return $result;
	}
	
	/*
	 * Validate email address
	 */
	function validateEmail($email) {

		return eregi("^[_\.0-9a-zA-Z-]+@([0-9a-zA-Z][0-9a-zA-Z-]+\.)+[a-zA-Z]{2,6}$", $email);
	}	
	
	
	/*
	 * Validate input by given regular exp..
	 */
	function validateRegExp($inputValue,$regExp){
		if(preg_match($regExp, $inputValue)){
			return true;
		}	
		
		return false;
	}
	
	function validateSMTP(&$validateObj){
		
		set_include_path(dirname(__FILE__)."/../lib/PEAR");
        require_once "Mail.php";
        
        $inputValues = $validateObj->getVariableValue();

		// build the email headers
		$headers = array('From' => $inputValues['email'],
						 'To' => $inputValues['email'],
						 'Subject' =>"Web Tool SMTP Validation Testing Email.");
		
		$authParams = array('host' => $inputValues['host'],
							'auth' => $inputValues['auth'],
                       	  	'username' => $inputValues['username'],
                       	  	'password' => $inputValues['password']);
		
		$mailing = Mail::factory('smtp', $authParams);
		$message = "Dear User!\n\n"
					."If you received this email, your smtp server setup is successful.\n\n"
					."Thanks";
		
		$mail = $mailing->send($inputValues['email'], $headers, $message);
		
		if(PEAR::isError($mail)){
			$validateObj->setErrorOutputMessage($mail->getMessage());
			return false;
		}
		return true;
	}
	
}

/**
 * 
 * @author erichou
 * 
 * This is the base class for each validator
 *
 */

/** Default error messages*/
define("REQUIRED_VALUE", "Field can not be empty.");
define("MAXLEN_EXCEEDED", "Please enter an input with length less than %d.");
define("MINLEN_CHECK_FAILED", "Please enter an input with length more than %d.");
define("EMAIL_CHECK_FAILED", "Please provide a valid email address.");
define("NUM_CHECK_FAILED", "Please provide a numeric input.");
define("ALPHA_CHECK_FAILED", "Please provide a alphabetic input.");
define("ALPHA_S_CHECK_FAILED", "Input can only contain alphabetic and space characters.");
define("ALNUM_S_CHECK_FAILED", "Input can only contain alpha-numeric and space characters.");
define("FLOAT_CHECK_FAILED", "Input can only be integer or float.");
define("FLOAT_D_CHECK_FAILED", "Float input can only with exactly %d decimal places.");
define("SMTP_CHECK_FAILED", "SMTP Server checking failed. Please contact your system administrator.");


// This is an inner class for formValidator.
class validatorObj{
	private $variableName;			// name of the variable
	private $variableValue;			// value of the variable
	private $validatorType;			// validation type
	private $typeOption;			// Value of the type if any
	private $errorOutputMessage;	// out put error message
	
	public function setVariableName($name){
		$this->variableName = $name;
	}
	
	public function getVariableName(){
		return $this->variableName;
	}
	
	public function setVariableValue($value){
		$this->variableValue = $value;
	}
	
	public function getVariableValue(){
		return $this->variableValue;
	}
	
	public function setValidatorType($type){
		
		$splitted = explode("=", $type);	
		
		$this->validatorType = $splitted[0];
		
		if(isset($splitted[1]) && strlen($splitted[1] > 0))
			$this->setTypeOption($splitted[1]);
		
	}

	public function setTypeOption($option){
		$this->typeOption = $option;
	}
	
	public function getTypeOption(){
		return $this->typeOption;
	}
	
	public function getValidatorType(){
		return $this->validatorType;
	}
	
	// setup the default error message if not provied
	public function setErrorOutputMessage($errmsg){
		if(empty($errmsg)){
			switch($this->getValidatorType()){
				
				case 'req':		{ $this->errorOutputMessage = REQUIRED_VALUE; break;	}
			
				case 'maxlen':	{ $this->errorOutputMessage = sprintf(MAXLEN_EXCEEDED, $this->getTypeOption()); break;	}
			
				case 'minlen':	{ $this->errorOutputMessage = sprintf(MINLEN_CHECK_FAILED, $this->getTypeOption()); break;	}
			
				case 'email':	{ $this->errorOutputMessage = EMAIL_CHECK_FAILED; break;	}
			
				case 'num':		{ $this->errorOutputMessage = NUM_CHECK_FAILED; break;	}

				case 'alpha':	{ $this->errorOutputMessage = ALPHA_CHECK_FAILED; break;	}
			
				case 'alpha_s':	{ $this->errorOutputMessage = ALPHA_S_CHECK_FAILED; break;	}
			
				case 'alnum_s':	{ $this->errorOutputMessage = ALNUM_S_CHECK_FAILED; break;	}
				
				case 'float':	{ $this->errorOutputMessage = FLOAT_CHECK_FAILED; break;	}
				
				case 'float_d':	{ $this->errorOutputMessage = sprintf(FLOAT_D_CHECK_FAILED, $this->getTypeOption()); break;	}
				
				case 'smtp':	{ $this->errorOutputMessage = SMTP_CHECK_FAILED; break;	}
		
			} //end switch			
		}
		else{
			$this->errorOutputMessage = $errmsg;
		}
	}
	
	public function getErrorOutputMessage(){
		return $this->errorOutputMessage;
	}

}

?>