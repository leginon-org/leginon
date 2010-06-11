<?php
define('SETUP_BASE', "setupBase.php");	//define the step1 filename
define('CONFIG_FILE', "../config.php");	//define config.php location
define('CONFIG_TEMPLATE', "../config.php.template");

require_once("../inc/mysql.inc");

if(file_exists(CONFIG_FILE)){
	require_once(CONFIG_FILE);
}

class setupUtils{

	var $basePath;		// BASE_PATH
	var $baseURL;		// BASE_URL
	var $projectURL;	// PROJECT_URL

	/*
	 * This function set Base Path base on the whole URL
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
	 * This function sets Base URL based on Base Path
	 */
	private function setBaseURL(){

		$this->baseURL = "/".$this->basePath."/";
	}

	/*
	 * This function sets Project URL based on Base URL
	 */
	private function setProjectURL(){

		$this->projectURL = $this->baseURL."project/";
	}

	/*
	 * This function will check the post variable value
	 * if the value is empty. we need to redirect back to
	 * the step 1.
	 */
	static function stepValidation(){

	}

	/*
	 * copyFiles function will copy the file1 to file2
	 * return true if copy sucessfully.
	 * otherwise return false
	 */
	static function copyFiles($file1, $file2){
		if(empty($file1))
			return false;
		$result = @copy($file1, $file2);
		return $result;
	}
	
	/*
	 * Create 
	 * 
	 */
	static function redirect($distPage){
		
		$host  = $_SERVER['HTTP_HOST'];
		$uri   = rtrim(dirname($_SERVER['PHP_SELF']), '/\\');

		return header("Location: http://$host$uri/$distPage");
	}

	/*
	 * The static function is going to check if the
	 * input file is exist on the file system.
	 * Return true if the file is there
	 * otherwise return false
	 */
	static function checkFile($fileLocation){

		if(empty($fileLocation))
			return false;

		$fileHandle = @fopen($fileLocation, 'r');
		if($fileHandle === false)
			return false;

		fclose($fileHandle);

		return true;
	}

	function fileToArray($fileLocation){

		if(empty($fileLocation))
			return "Please provide the file location";

		$fileHandle = fopen($fileLocation, 'r') or die("Can't open input file");
		$i = 0;
		while(!feof($fileHandle)){
			$fileContent[$i] = fgets($fileHandle);
			$i++;
		}
		fclose($fileHandle);

		return $fileContent;

	}

	/*
	 * Function will take an array of content and array of inputs
	 * The output will become a key, value pair array.
	 * keys are $inputs, $values are from $arrayOfContent
	 * PS: We only want to find php Constant.
	 * define("DB_USER", "dbuser");
	 */
	function searchValuesByInputsInArray($arrayOfContent, $inputs){

	}

	/*
	 * This function take a file location and all the variables
	 * need to change or edit. It will fill in all the changes
	 * base on the input $params
	 * $configFile: The location of the file
	 * $params: Value, key pair array.
	 */
	function editConfigFile($configFile, $params){

		$matchingStrings = Array("define", "addplugin", "PROCESSING_HOSTS", "CLUSTER_CONFIGS");

		if(empty($params) || !is_array($params)) return false;

		$fileHandle = @fopen($configFile, 'r') or die("Can't open config.php file");
		$i = 0;
		while(!feof($fileHandle)){

			$lineOfText = fgets($fileHandle);

			//put every line to an array
			$newline = $this->fillinDefineConstant($lineOfText, $matchingStrings, $params);

			$fileContent[$i] = $newline;
			$i++;
		}

		fclose($fileHandle);

		return $fileContent;
	}

	function arrayToFile($configFile, $fileContent){

		if(empty($configFile) && empty($fileContent))
			return false;

		$fileHandle = @fopen($configFile, 'w') or die("Can't open or write config.php file");

		foreach($fileContent as $content){
			fwrite($fileHandle, $content);
		}

		fclose($fileHandle);
		return true;
	}

	/*
	 * This function is going to fill in the line with input value.
	 * right now it will do constant and plugins
	 * $inputString : The String need to update if match
	 * $matchingStrings: An array of strings need to match with $inputString
	 * $params: An array of Key and Value information need to fillin the inputString
	 */
	private function fillinDefineConstant($inputString, $matchingStrings, $params){

		// if input string contain nothing. just return it.
		if(empty($inputString))	return $inputString;

		foreach($matchingStrings as $matchingString){

			// if the matchingString is in the php title commenting which
			// start with // --- , we want to skip it.
			$titleCommenting = stripos($inputString, "// ---");
			if($titleCommenting !== false) return $inputString;

			$pos1 = stripos($inputString, $matchingString);
			// when found matching string, get out of loop.
			if($pos1 !== false)	break;

		}
		// nothing match with matchingString, just return the original string.
		if($pos1 === false)	return $inputString;

		// loop through each params. find matching one and change the string and break the loop.
		// if can't find the matching one, just keep looping until the last param.
		foreach($params as $key => $value){

			if($matchingString == "define"){

				$key = "'".strtoupper($key)."'";

				$pos2 = strpos($inputString, $key);
				// once found constant and build the String, break out the loop
				if($pos2 !== false){
						// rebuild the original string once everything match.
						// Can't use boolean check. because $value is from html post.
					if($value == "true" || $value == "false")
						// build boolean constant.
						$inputString = "$matchingString($key, $value);\n";
					else
						// build string constant.
						$inputString = "$matchingString($key,\"$value\");\n";
					break;
				}
			}elseif($matchingString == "addplugin"){

				$pos2 = strpos($inputString, $key);

				// when found the match and the plugin is set to true
				// enable this plugin.
				if($pos2 !== false){

					$inputString = ($value == "true") ?
						$matchingString."(\"".$key."\");\n" : "// ".$matchingString."(\"".$key."\");\n";
					break;
				}
			}
			// need to construct $PROCESSING_HOST[].
			elseif($matchingString == "PROCESSING_HOSTS"){

				$key = "$".strtoupper($key)."[]";

				$pos2 = strpos($inputString, $key);

				if($pos2 !== false){
					$inputString = "";
					foreach($value as $name)
						// build this string:
						// $PROCESSING_HOSTS[] = array('host' => 'host1.school.edu', 'nproc' => 8);
						$inputString .= $key." = array('host' => '".$name['host']."', 'nproc' => ".$name['nproc'].");\n";
					break;
				}
			}
			// need to construct $CLUSTER_CONFIGS= array ('');
			elseif($matchingString == "CLUSTER_CONFIGS"){

				$key = "$".strtoupper($key)."[]";

				$pos2 = strpos($inputString, $key);

				if($pos2 !== false){
					$inputString = "";

					foreach($value as $name)
						// build this string:
						// $CLUSTER_CONFIGS[]= 'cluster1';
						$inputString .= $key." = '".$name."';\n";

					break;
				}
			}
		}

		return $inputString;
	}

	/*
	 * This function is going to check if the session has been created
	 * or has been expire. When there is no setup Session, redirect
	 * to the index page. and also double
	 */
	static function checkSession(){

		session_start();
		if(empty($_SESSION)){
			setupUtils::redirect('index.php');
			exit();
		}

		// if session has been create more than 30 min. destroy it.
		if(time() - $_SESSION['time'] > 1800){	
			session_destroy();
			setupUtils::checkSession();
		}
		// reset the time
		$_SESSION['time'] = time();

	}

	function checkDBConnection($dbHost, $dbUsername, $dbPassword) {

		$mysqld = new mysql($dbHost, $dbUsername, $dbPassword);
		$result = $mysqld->connect_db();

		return $result;
	}

	function checkDBExist($dbHost, $dbUsername, $dbPassword, $db) {

		$link = $this->checkDBConnection($dbHost, $dbUsername, $dbPassword);

		$db = mysql_select_db($db, $link);
		mysql_close($link);
		if(!$db)
			return false;
		//$result = $this->select_db($db, $link);
		return true;
	}

	//static function
}


