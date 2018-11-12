<?php
#####################################################################
#
# phpextensions is a class that was found here:
# http://www.wlscripting.com/tutorial/47
#
# It is a quick way to get info about the extensions loaded in php.
#
######################################################################
require_once('moduleCheck.inc');
require_once("../inc/mysql.inc");


#####################################################################
#
# The WebServerTester class contains functions to test that the 
# Appion/Leginon web server has been properly configured. The
# meat of most of these tests are found in other like PHP extensions
# or PHP itself. This class adds value by providing error messages 
# that are tailored to Appion/Leginon based on very specific 
# problems with the installation. Please keep this file free of 
# HTML formatting if possible.
#
#####################################################################
class WebServerTester 
{
	private $modules;

	function __construct() {
		$this->modules = new moduleCheck();
	}

	#####################################################################
	#
	# Check the version of PHP
	# Parameter $minPhpVersion should be a string such as "5.1.6"
	#
	#####################################################################
	function verifyPHPVersion( $minPhpVersion, $maxPhpVersion = NULL ) 
	{
		//Get the currently running PHP version
		$phpVersion = phpversion();

		if (strnatcmp($phpVersion,$minPhpVersion) < 0)
		{
			// not sufficiant version
			throw new Exception("!!! WARNING !!! PHP version $phpVersion is too old. Please upgrade to  $minPhpVersion.");
		}
		
		if (!is_null($maxPhpVersion)) 
		{
			if (strnatcmp($phpVersion,$maxPhpVersion) >= 0)
			{
				// version is not yet supported
				throw new Exception("!!! WARNING !!! PHP version $phpVersion is too new. Please downgrade to a version older than $maxPhpVersion.");
			}
		}

		return $phpVersion;
	}


	#####################################################################
	#
	# Test that gd is loaded
	#
	# TODO: Check for tiff support enabled
	#
	#####################################################################
	function verifyGdLib() 
	{
		if (extension_loaded('gd')) {
			// See if jpeg support is enabled
			$jpgEnabled = $this->modules->getModuleSetting('gd','JPG Support');
			// newer versions changed the name
			$jpegEnabled = $this->modules->getModuleSetting('gd','JPEG Support');
			
			if ($jpegEnabled != 'enabled' && $jpgEnabled != 'enabled') {
				throw new Exception("!!! WARNING !!! JPEG support is not enabled for the GD php extension. For more info about installing the jpeg library, see: http://www.php.net/manual/en/image.requirements.php");
			}
		} else {
			throw new Exception("!!! WARNING !!! The php-gd library is not installed. Find more info here: http://emg.nysbc.org/redmine/projects/appion/wiki/Install_Web_Server_Prerequisites");
		}
		
		return $this->modules->getModuleSetting('gd');
	}

	#####################################################################
	#
	# test that ssh2 is installed
	#
	#####################################################################
	function verifySSH2() 
	{
		if (!extension_loaded('ssh2'))
		{
			throw new Exception("!!! WARNING !!! The php ssh2 extension is NOT loaded. See http://emg.nysbc.org/redmine/projects/appion/wiki/Install_SSH_module_for_PHP.");
		}
		return true;
	}

	#####################################################################
	#
	# Test if mrc is loaded and fftw3 is enabled
	# Returns the MRC module settings if verification is successful.
	#
	#####################################################################
	function verifyMRC() 
	{
		if($this->modules->isLoaded('mrc')) {
			// See if fftw is enabled
			$fftwEnabled = $this->modules->getModuleSetting('mrc','FFTW3 support');
			
			if ($fftwEnabled != 'enabled') {
				throw new Exception("!!! WARNING !!! FFTW3 is not enabled for the MRC php extension. For more info see: http://emg.nysbc.org/redmine/projects/appion/wiki/Install_Web_Server_Prerequisites");
			}
		} else {
			throw new Exception("!!! WARNING !!! MRC php extension is not loaded. For more info see: http://emg.nysbc.org/redmine/projects/appion/wiki/Install_the_MRC_PHP_Extension");
		}
		
		return $this->modules->getModuleSetting('mrc');
	}

	#####################################################################
	#
	# returns the contents of a file in an array. 
	#
	# throws exceptions if file not found or could not open.
	#
	# Takes parameter $fileLocation which is the path to the config file.
	#
	#####################################################################
	function readFromFile( $fileLocation ) 
	{	
		$filename = basename($fileLocation);
		
		// Ensure the file exists
		if ( file_exists($fileLocation)) {
			$fileHandle = fopen($fileLocation, 'r');
			
			// Ensure the file was properly opened
			if (!$fileHandle) {
				throw new Exception("!!! WARNING !!!  Could not open your $filename file located at $fileLocation. ");
			}
		} else {
			throw new Exception("!!! WARNING !!!  Could not find your $filename file at $fileLocation. You may create a config file at http://YOUR_HOST/myamiweb/setup.");
		}
	
		// read the contents of the file into an array
		$i = 0;
		while( $line = fgets($fileHandle)){
			$fileContent[$i] = $line;
			$i++;
		}
		fclose($fileHandle);
		
		return $fileContent;			
	}
	
	#####################################################################
	#
	# Ensure there are no blank lines at the end of config.php
	#
	# Takes parameter $fileLocation which is the path to the config file.
	# Returns true if the file ends with PHP close tag rather than a 
	# blank line.
	#
	#####################################################################
	function verifyConfig( $fileLocation ) 
	{	
		try {
			$fileContent = $this->readFromFile( $fileLocation );
		} catch(Exception $e) {
			throw new Exception( $e->getMessage()." You may create a config file at http://YOUR_HOST/myamiweb/setup." );
		}

		// Get the last line of the config file
		$lastLine = array_pop( $fileContent );

		// The last line should be the php close tag, anything else is unacceptable, 
		// including white space after the tag on the same line as the tag.
		$closeTag = "?>\n";
		$compareResult = strcmp( $lastLine, $closeTag );
		similar_text($lastLine, $closeTag, $p);
		if ($compareResult !== 0)
		{
			throw new Exception("!!! WARNING !!! The final line of your config.php file ($lastLine) may cause images to not be displayed properly. Please remove any blank lines or spaces that occur after the final tag.");
		}
		
		return true;
	}
	
	#####################################################################
	#
	# return an array containing the config file
	#
	# Takes parameter $fileLocation which is the path to the config file.
	# Does not display username or password information.
	#
	#####################################################################
	function printConfig( $fileLocation ) 
	{	
		try {
			$fileContent = $this->readFromFile( $fileLocation );
		} catch(Exception $e) {
			throw new Exception( $e->getMessage()." You may create a config file at http://YOUR_HOST/myamiweb/setup." );
		}

		// strip out lines regarding usernames or passwords (a bit aggressively for now)
		foreach ( $fileContent as $line ) {
			if ( (stripos( $line, "user" ) === false) && (stripos( $line, "pass" ) === false) ) {
				$displayArray[] = $line;
			}
		}
		
		return $displayArray;
	}
	
	#####################################################################
	#
	# Get the version and revision numbers from the project database
	#
	# Takes parameter $fileLocation which is the path to the config file.
	# Returns a message as a string with the version and revision. 
	# TODO: This is a lame way to return the data but quick. Refactor me.
	#
	#####################################################################
	function getDBVersion( $fileLocation ) 
	{
		if (file_exists($fileLocation)){
			require_once($fileLocation);
		} else {
			throw new Exception("!!! WARNING !!!  Could not find your config.php file at $fileLocation. You may create a config file at http://YOUR_HOST/myamiweb/setup.");
		}
	
		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();

		if ($dbLink == false) {	
			throw new Exception("!!! WARNING !!!  Cannot connect to the database server with db_host: ".DB_HOST." db_usr : ".DB_USER);
		}
		
		$result = $mysqld->select_db(DB_PROJECT, $dbLink);
		if($result == false) {
			throw new Exception("!!! WARNING !!!  \"".DB_PROJECT."\" database does not exist.");
		}
	
		// find the current version and revision numbers 
		$versionresults = $mysqld->getSQLResult('select `key`, value from install where `key` = \'version\'');
		$revisionresults = $mysqld->getSQLResult('select `key`, value from install where `key` = \'revision\'');
		
		$message = "Unable to find the current Appion version and revision numbers in the \"".DB_PROJECT."\" database.";
		if( (!empty($versionresults)) && (!empty($revisionresults)) ){					
			foreach($versionresults as $result){
				$currentDBVersion = $result['value'];
			}
			foreach($revisionresults as $result){
				$currentDBRevision = $result['value'];
			}
			if(!empty($currentDBVersion) && !empty($currentDBRevision)) {
				$message = 'Your current Appion version is '.$currentDBVersion.' and revision is '.$currentDBRevision;
			}
		}
		
		$mysqld->close_db($dbLink);
		
		return $message;
	}
	
}
?>
