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
class WebServerTester {

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
	function verifyPHPVersion( $minPhpVersion, $maxPhpVersion = NULL ) {

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
	function verifyGdLib() {
		if (extension_loaded('gd')) {
			// See if jpeg support is enabled
			$jpegEnabled = $this->modules->getModuleSetting('gd','JPG Support');
			
			if ($jpegEnabled != 'enabled') {
				throw new Exception("!!! WARNING !!! JPEG support is not enabled for the GD php extension. For more info about installing the jpeg library, see: http://www.php.net/manual/en/image.requirements.php");
			}
		} else {
			throw new Exception("!!! WARNING !!! The php-gd library is not installed. Find more info here: http://ami.scripps.edu/redmine/projects/appion/wiki/Install_Web_Server_Prerequisites");
		}
		
		return $this->modules->getModuleSetting('gd');
	}

	#####################################################################
	#
	# test that ssh2 is installed
	#
	#####################################################################
	function verifySSH2() {
		if (!extension_loaded('ssh2'))
		{
			throw new Exception("!!! WARNING !!! The php ssh2 extension is NOT loaded. See http://ami.scripps.edu/redmine/projects/appion/wiki/Install_SSH_module_for_PHP.");
		}
		return true;
	}

	#####################################################################
	#
	# Test if mrc is loaded and fftw3 is enabled
	# Returns the MRC module settings if verification is successful.
	#
	#####################################################################
	function verifyMRC() {

		if($this->modules->isLoaded('mrc')) {
			// See if fftw is enabled
			$fftwEnabled = $this->modules->getModuleSetting('mrc','FFTW3 support');
			
			if ($fftwEnabled != 'enabled') {
				throw new Exception("!!! WARNING !!! FFTW3 is not enabled for the MRC php extension. For more info see: http://ami.scripps.edu/redmine/projects/appion/wiki/Install_Web_Server_Prerequisites");
			}
		} else {
			throw new Exception("!!! WARNING !!! MRC php extension is not loaded. For more info see: http://ami.scripps.edu/redmine/projects/appion/wiki/Install_the_MRC_PHP_Extension");
		}
		
		return $this->modules->getModuleSetting('mrc');
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
	function verifyConfig( $fileLocation ) {	
	
		// Ensure the config file exists
		if ( file_exists($fileLocation)) {
			$fileHandle = fopen($fileLocation, 'r');
			
			// Ensure the file was properly opened
			if (!$fileHandle) {
				throw new Exception("!!! WARNING !!!  Could not open your config.php file located at $fileLocation. ");
			}
		} else {
			throw new Exception("!!! WARNING !!!  Could not find your config.php file at $fileLocation. You may create a config file at http://YOUR_HOST/myamiweb/setup.");
		}
	
		// read the contents of the file into an array
		$i = 0;
		while(!feof($fileHandle)){
			$fileContent[$i] = fgets($fileHandle);
			$i++;
		}
		fclose($fileHandle);
	
		//Check the last entry to make sure it is not blank
		$lastLine = $fileContent[$i-1];

		// The last line should be the php close tag, anything else is unacceptable.
		if ($lastLine != "?>")
		{
			throw new Exception("!!! WARNING !!! The final line of your config.php file ($lastLine) may cause images to not be displayed properly. Please remove any blank lines that occur after the final  tag.");
		}
		
		return true;
	}
}
?>