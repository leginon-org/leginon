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
	 * MaxValue : 
	 * 				addValidation("variableName", "variableValue", "maxval=10");
	 * 				addValidation("variableName", "variableValue", "maxval=10", "Your own error message");
	 * MinValue : 
	 * 				addValidation("variableName", "variableValue", "minval=3");
	 * 				addValidation("variableName", "variableValue", "minval=3" , "Your own error message");
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
	 * absolute path: path_exist
	 * 				addValidation("variableName", "Path Location", "abs_path");
	 * 				addValidation("variableName", "Path Location", "abs_path", "Your own error message");
	 * 
	 * path existence
	 * 				addValidation("variableName", "Path Location", "path_exist");
	 * 				addValidation("variableName", "Path Location", "path_exist", "Your own error message");
	 * 
	 * folder permission
	 * 				addValidation("variableName", "Folder Location", "folder_permission");
	 * 				addValidation("variableName", "Folder Location", "folder_permission", "Your own error message");
	 * 
	 * file existence
	 * 				addValidation("variableName", "File location", "file_exist");
	 * 				addValidation("variableName", "File Location", "file_exist", "Your own error message");
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
	 * Exclude : 
	 * 				addValidation("variableName", "variableValue", "exclude=otherVariableName,otherVariableValue", "Your own error message");
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
	
	function setErrorMessage($variableName, $errorMessage){
		$this->errorMessages[$variableName] = $errorMessage;
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

				$this->setErrorMessage($validateObj->getVariableName(), $validateObj->getErrorOutputMessage());
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
			
			case 'maxval':{
				$result = $this->validateMaxval($validateObj->getVariableValue(), $validateObj->getTypeOption());
				break;
			}
			
			case 'minval':{
				$result = $this->validateMinval($validateObj->getVariableValue(), $validateObj->getTypeOption());
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
				$result = $this->validateRegExp($validateObj->getVariableValue(), "/^\d+\.?\d*$/");
				break;
			}
			
			case 'abs_path':{
				$result = $this->validateRegExp($validateObj->getVariableValue(), "#^/[\w/\-]*$#");
				break;
			}
			
			case 'path_exist':{
				$result = $this->validatePathIsExist($validateObj->getVariableValue());
				break;
			}
			
			case 'folder_permission':{
				$result = $this->validateFolderPermission($validateObj->getVariableValue());
				break;
			}
			
			case 'file_exist':{
				$result = $this->validatefileExist($validateObj->getVariableValue());
				break;
			}
			
			case 'float_d':{
				$numberOfDecimal = $validateObj->getTypeOption();
				
				$floatRegExp = "/^\d*\.\d{". $numberOfDecimal ."}$/";
				$result = $this->validateRegExp($validateObj->getVariableValue(), $floatRegExp);
				break;
			}
			
			case 'database':{
				$result = $this->validateDB($validateObj);
				break;
			}
			
			case 'remoteServer':{
				$result = $this->validateRemoteServer($validateObj);
				break;
			}
			
			case 'smtp':{
				$result = $this->validateSMTP($validateObj);
				break;
			}
			
			case 'noquote':{
				$result = $this->validateNoQuote($validateObj->getVariableValue());
				break;
			}
			case 'exclude':{
				$splitted = explode(",", $validateObj->getTypeOption());	
				$other_value = $splitted[1];
				$result = $this->validateExclude($validateObj->getVariableValue(),$other_value);
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
	 * Validate "noquote" field
	 * This will allow quotes as the first and last chars, but nothing in between.
	 */
	function validateNoQuote($inputValue){
		$result = true;

		// remove the first and last chars, it is fine if these are quote chars, as this is generally
		// necessary if there is a space within the string
		$str = substr( $inputValue, 1, -1 );
		
		if (  (strlen($str) > 0) && (strpos( $str, "'" ) !== false || strpos( $str, '"' ) !== false) ) {
      		$result = false;
		}		

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
	 * Validate Max value of input value
	 */
	function validateMaxval($inputValue, $maxval){
		
		$result = true;
		
		if ( isset($inputValue) ) {			
			if ($inputValue > $maxval)				
				$result=false;
		}
		return $result;
	}
	
	/*
	 * Validate Min value of input value
	 */
	function validateMinval($inputValue, $minval){
		
		$result = true;
		
		if ( isset($inputValue) ) {
			
			if ($inputValue < $minval)
				$result=false;
		}
		return $result;
	}
	
	/*
	 * Validate email address
	 */
	function validateEmail($email) {

		return preg_match("%^[_\.0-9a-zA-Z-]+@([0-9a-zA-Z][0-9a-zA-Z-]+\.)+[a-zA-Z]{2,6}$%i", $email);
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
	
	function validateExclude($inputValue,$otherValue){
		//One way exclusion
		//empty string is considered set.  Check string length as well
		//to include 0 and "0".
		if( isset($otherValue) && strlen($otherValue) > 0 ){
			// Must not set $inputValue if $otherValue is set
			if ( isset($inputValue) && strlen($inputValue) > 0 )
				return false;
		}
		
		return true;
	}
	
	/*
	 * Check if the input path is exist
	 * return true if exist
	 * otherwise return false
	 */
	function validatePathIsExist($path){
		if(is_dir($path))
			return true;
			
		return false;
	}
	
	/*
	 * Check if the apache user has write permission to the input folder
	 * return true if apache has write access to the folder
	 * otherwise return false
	 */
	function validateFolderPermission($folderLocation){
		
		$result = @mkdir($folderLocation."/validationTesting", 777);
		
		if($result){
			rmdir($folderLocation."/validationTesting");
			return true;
		}
		return false;
	}
	
	/*
	 * Check if the file is exist in the given location
	 * return true if exist
	 * otherwise return false.
	 */
	function validatefileExist($fileLocation){
		if(file_exists($fileLocation))
			return true;
			
		return false;
	}
	
	function validateRemoteServer(&$validateObj){
		
		$extensions = get_loaded_extensions();
		
		if(in_array('ssh2', $extensions)){
		
			$defaultPort = 22;
		
			$result = @ssh2_connect($validateObj->getVariableValue(), $defaultPort);
		
			if($result)
				return true;
			return false;
			
		}
		
		$validateObj->setErrorOutputMessage("PHP 'ssh2' module is required to setup local cluster.");
		return false;
	}
	
	/*
	 * Validate the SMTP server connection.
	 * If there have any error, get the error message for display.
	 * otherwise, this function will send an testing email via smtp server
	 * to the email account user provided.
	 * 
	 */
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
					."If you received this email, your smtp server setup for Appion and/or Leginon is successful.\n\n"
					."Thanks";
		
		$mail = $mailing->send($inputValues['email'], $headers, $message);
		
		if(PEAR::isError($mail)){
			$validateObj->setErrorOutputMessage($mail->getMessage());
			return false;
		}
		return true;
	}
	
	/*
	 * Validate database connection and existence of the Leginon database and Project database.
	 */
	function validateDB(&$validateObj){

		require_once(dirname(__FILE__)."/mysql.inc");
		
		$inputValues = $validateObj->getVariableValue();
		
		$mysqld = new mysql($inputValues['host'], $inputValues['username'], $inputValues['password']);
		$dbLink = $mysqld->connect_db();
		
		if($dbLink == false) {
			
			$validateObj->setErrorOutputMessage("Cannot connect to the database server with the following 'hostname', 'username' and 'password'.");
			return false;
		}
		
		$dbSelectResult = $mysqld->select_db($inputValues['leginondb'], $dbLink);
		
		if($dbSelectResult == false) {
			$validateObj->setErrorOutputMessage("Leginon database does not exist or you have entered the wrong database name.");
			$mysqld->close_db($dbLink);
			return false;
		}
		
		$dbSelectResult = $mysqld->select_db($inputValues['projectdb'], $dbLink);
		
		if($dbSelectResult == false) {
			$validateObj->setErrorOutputMessage("Project database does not exist or you have entered the wrong database name.");
			$mysqld->close_db($dbLink);
			return false;
		}
		
		$mysqld->close_db($dbLink);
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
define("MAXVAL_EXCEEDED", "Please enter a value no greater than %d.");
define("MINVAL_CHECK_FAILED", "Please enter a value no less than %d.");
define("EMAIL_CHECK_FAILED", "Please provide a valid email address.");
define("NUM_CHECK_FAILED", "Please provide a positive integer input.");
define("ALPHA_CHECK_FAILED", "Please provide an alphabetic input.");
define("ALPHA_S_CHECK_FAILED", "Input can only contain alphabetic and space characters.");
define("ALNUM_S_CHECK_FAILED", "Input can only contain alpha-numeric and space characters.");
define("FLOAT_CHECK_FAILED", "Input can only be an integer or float.");
define("FLOAT_D_CHECK_FAILED", "Float input must have exactly %d decimal places.");
define("ABS_PATH_CHECK_FAILED", "Input has to be an absolute path.");
define("PATH_EXIST_CHECK_FAILED", "The input path does not exist on the machine.");
define("FILE_EXIST_CHECK_FAILED", "The file does not exist at the given location.");
define("FOLDER_PERMISSION_CHECK_FAILED", "Apache user does not have write permission on the following path.");
define("SMTP_CHECK_FAILED", "SMTP Server checking failed. Please contact your system administrator.");
define("REMOTE_SERVER_CHECK_FAILED", "REMOTE Server checking failed. Please contact your system administrator.");
define("DATABASE_CHECK_FAILED", "Database checking failed. Please contact your system administrator.");
define("REMOVE_QUOTE_CHAR", "Please remove any quote characters from your entry.");
define("EXCLUDE_CHECK_FAILED", "Can not coexist with %s set to '%s'");

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
	
		if(isset($splitted[1]) && strlen($splitted[1]))
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
				
				case 'req':			{ $this->errorOutputMessage = REQUIRED_VALUE; break;	}
			
				case 'maxlen':		{ $this->errorOutputMessage = sprintf(MAXLEN_EXCEEDED, $this->getTypeOption()); break;	}
			
				case 'minlen':		{ $this->errorOutputMessage = sprintf(MINLEN_CHECK_FAILED, $this->getTypeOption()); break;	}
			
				case 'maxval':		{ $this->errorOutputMessage = sprintf(MAXVAL_EXCEEDED, $this->getTypeOption()); break;	}
			
				case 'minval':		{ $this->errorOutputMessage = sprintf(MINVAL_CHECK_FAILED, $this->getTypeOption()); break;	}
				
				case 'email':		{ $this->errorOutputMessage = EMAIL_CHECK_FAILED; break;	}
			
				case 'num':			{ $this->errorOutputMessage = NUM_CHECK_FAILED; break;	}

				case 'alpha':		{ $this->errorOutputMessage = ALPHA_CHECK_FAILED; break;	}
			
				case 'alpha_s':		{ $this->errorOutputMessage = ALPHA_S_CHECK_FAILED; break;	}
			
				case 'alnum_s':		{ $this->errorOutputMessage = ALNUM_S_CHECK_FAILED; break;	}
				
				case 'float':		{ $this->errorOutputMessage = FLOAT_CHECK_FAILED; break;	}
				
				case 'float_d':		{ $this->errorOutputMessage = sprintf(FLOAT_D_CHECK_FAILED, $this->getTypeOption()); break;	}
				
				case 'abs_path':	{ $this->errorOutputMessage = ABS_PATH_CHECK_FAILED; break;	}
				
				case 'path_exist':	{ $this->errorOutputMessage = PATH_EXIST_CHECK_FAILED; break;	}
				
				case 'folder_permission':{ $this->errorOutputMessage = FOLDER_PERMISSION_CHECK_FAILED; break;}
				
				case 'file_exist':	{ $this->errorOutputMessage = FILE_EXIST_CHECK_FAILED; break;	}
			
				case 'smtp':		{ $this->errorOutputMessage = SMTP_CHECK_FAILED; break;	}
				
				case 'remoteServer': { $this->errorOutputMessage = REMOTE_SERVER_CHECK_FAILED; break; }
				
				case 'database':	{ $this->errorOutputMessage = DATABASE_CHECK_FAILED; break;	}
				
				case 'noquote':	{ $this->errorOutputMessage = REMOVE_QUOTE_CHAR; break;	}
				case 'exclude':		{ 
					$splitted = explode(",", $this->getTypeOption());	
					$other_variable = $splitted[0];
					$other_value = $splitted[1];
					$this->errorOutputMessage = sprintf(EXCLUDE_CHECK_FAILED, $other_variable,$other_value); break;	
				}
				
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
