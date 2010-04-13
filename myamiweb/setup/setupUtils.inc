<?php 
define('PROJECT_NAME', "myamiweb");		//session variable.
define('SETUP_BASE', "setupBase.php");	//define the step1 filename

class setupUtils{
	
	var $basePath;		// BASE_PATH
	var $baseURL;		// BASE_URL
	var $projectURL;	// PROJECT_URL
	
	/*
	 * 
	 */
	function setBasePath($fullpath){
		
		$result = str_replace("/setup/".SETUP_BASE, "", $fullpath);
		
		if($result[0] == '/')
			$result = substr($result, 1);
		
		$this->basePath = $result;
		$this->setBaseURL();
		$this->setProjectURL();
	}
	
	/*
	 * 
	 */
	function setBaseURL(){
		
		$this->baseURL = "/".$this->basePath."/";
	}
	
	/*
	 * 
	 */
	function setProjectURL(){

		$this->projectURL = $this->baseURL."project";
	}
	
	/*
	 * This function will check the post variable value
	 * if the value is empty. we need to redirect back to
	 * the step 1.
	 */
	function stepValidation(){
		
	}
	
}
?>