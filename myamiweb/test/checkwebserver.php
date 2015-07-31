<html>
<head>
	<link href="../css/viewer.css" media="all" rel="stylesheet" type="text/css" />
</head>
<body>
<?php
#####################################################################
#
# This file is used to present to the user in a web browser
# warnings related to the setup of the Appion/Leginon web server.
#
# TODO: Add checks for processing server prereqs. Not sure which
#       ones are required???
#
# There are several hard coded constants in this file that may need to be maintained:
# 1. $configFileLocation - the path to the config.php file
# 2. $minPhpVersion - minimum version of PHP required for Appion/Leginon
# 3. The php.ini recommended values
#
#####################################################################
require_once('../config.php');
require_once('../inc/login.inc');
login_header();

echo "<h2>Appion/Leginon Web Server Troubleshooting Tool</h2>";
echo "<p>";


#####################################################################
#
# phpextensions is a class that was found here:
# http://www.wlscripting.com/tutorial/47
#
# It is a quick way to get info about the extensions loaded in php.
#
######################################################################
require_once('./inc/moduleCheck.inc');
$modules = new moduleCheck();

require_once('./inc/webServerTester.inc');
$tester = new WebServerTester();

// The location of the config file
$configFileLocation = "../config.php";


#####################################################################
#
# Display the Appion version
#
#####################################################################
echo "<h3>Current Appion Version and Revision:</h3>";
echo "<p>";
try {
	echo $tester->getDBVersion($configFileLocation);
} catch(Exception $e) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "</p>";


#####################################################################
#
# Ensure there are no blank lines at the end of config.php
#
#####################################################################
echo "<h3>config.php file check:</h3>";
echo "<p>";

try {
	$tester->verifyConfig($configFileLocation);
	echo "Your config.php file is properly formatted.";
} catch(Exception $e) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "<p>";
echo "<a class='header' href='viewconfig.php' target='_blank'>[View Config File]</a>";

#####################################################################
#
# Check the version of PHP
#
#####################################################################
echo "<h3>PHP check:</h3>";
echo "<p>";

// The minimum version of PHP required for Appion/Leginon, inclusive
$minPhpVersion = "5.3.0";

// upper bound, exclusive. If it must be 5.2.x but not 5.3.x, the maxPhpVersion is 5.3.
$maxPhpVersion = "5.4.0"; 

try
{
	$phpVersion = $tester->verifyPHPVersion($minPhpVersion, $maxPhpVersion);
	echo "PHP version: $phpVersion";
} catch( Exception $e ) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "</p>";



#####################################################################
#
# Check that the php.ini has been properly modified
#
# error_reporting = E_ALL & ~E_NOTICE & ~E_WARNING
# display_errors = On
# register_argc_argv = On
# short_open_tag = On
# max_execution_time = 300 ; Maximum execution time of each script, in seconds
# max_input_time = 300 ; Maximum amount of time each script may spend parsing request data
# memory_limit = 256M ; Maximum amount of memory a script may consume (8MB)
#
#
#####################################################################
echo "<h3>php.ini check:</h3>";
echo "<p>";
echo "Use the table below to ensure your php.ini settings are correct. <br />";
echo "<a target='_blank' href='http://emg.nysbc.org/redmine/projects/appion/wiki/Configure_phpini'>[More info about php.ini settings]</a> <br />";
echo "<p>";

// These are constant values based on what AMI recommends for the php.ini settings
$errorReportingRec   = "22517";
$displayErrorsRec    = "On";
$registerArgcArgvRec = "On";
$shortOpenTagRec     = "On";
$maxExeTimeRec       = "300";
$maxInputTimeRec     = "300";
$memoryLimitRec      = "256M";

// Convert the error reporting value to something readable
// TODO: it may be better to read the php.ini file and get the string value.
//$errorReporting = get_cfg_var('error_reporting');
$errorReporting = ini_get('error_reporting');
switch ($errorReporting) {
	case 2039:
		$errorReportingText = "E_ALL & ~E_NOTICE";
		break;
	case 2037:
		$errorReportingText = "E_ALL & ~E_NOTICE & ~E_WARNING";
		break;
	case 2047:
		$errorReportingText = "E_ALL";
		break;
	case 22519:
		$errorReportingText = "E_ALL & ~E_DEPRECATED & ~E_NOTICE";
		break;
	case 22517:
		$errorReportingText = "E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING";
		break;
	default:
		$errorReportingText = $errorReporting;
}

// Get the rest of the current settings
$displayErrors    = get_cfg_var('display_errors') ? 'On' : 'Off';
$registerArgcArgv = get_cfg_var('register_argc_argv') ? 'On' : 'Off';
$shortOpenTag     = get_cfg_var('short_open_tag') ? 'On' : 'Off';
$maxExeTime       = get_cfg_var('max_execution_time');
$maxInputTime     = get_cfg_var('max_input_time');
$memoryLimit      = get_cfg_var('memory_limit');

// Set the font color for each setting. Red means the value is not the recommended value.
$errorColor = "red";
$textColor = "black";

$errorReportingFont   = ($errorReporting   != $errorReportingRec)   ? $errorColor : $textColor;
$displayErrorsFont    = ($displayErrors    != $displayErrorsRec)    ? $errorColor : $textColor;
$registerArgcArgvFont = ($registerArgcArgv != $registerArgcArgvRec) ? $errorColor : $textColor;
$shortOpenTagFont     = ($shortOpenTag     != $shortOpenTagRec)     ? $errorColor : $textColor;
$maxExeTimeFont       = ($maxExeTime       != $maxExeTimeRec)       ? $errorColor : $textColor;
$maxInputTimeFont     = ($maxInputTime     != $maxInputTimeRec)     ? $errorColor : $textColor;
$memoryLimitFont      = ($memoryLimit      != $memoryLimitRec)      ? $errorColor : $textColor;



?>
<!-- Build a table to display the php.ini settings  --> 
<table border='1'>
	<tr>
		<td><b>Setting</b></td>
		<td><b> Your php.ini Value </b></td>
		<td><b> Recommended Value </b></td>
	</tr>
	<tr>
		<td>error_reporting</td>
		<td><? echo "<font color='".$errorReportingFont."'>".$errorReportingText."</font>"; ?></td>
		<td>E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED</td>
	</tr>
	<tr>
		<td>display_errors</td>
		<td><? echo "<font color='".$displayErrorsFont."'>".$displayErrors."</font>"; ?></td>
		<td>On</td>
	</tr>
		<td>register_argc_argv</td>
		<td><? echo "<font color='".$registerArgcArgvFont."'>".$registerArgcArgv."</font>"; ?></td>
		<td>On</td>
	</tr>
		<td>short_open_tag</td>
		<td><? echo "<font color='".$shortOpenTagFont."'>".$shortOpenTag."</font>"; ?></td>
		<td>On</td>
	</tr>
		<td>max_execution_time</td>
		<td><? echo "<font color='".$maxExeTimeFont."'>".$maxExeTime."</font>"; ?></td>
		<td>300</td>
	</tr>
		<td>max_input_time</td>
		<td><? echo "<font color='".$maxInputTimeFont."'>".$maxInputTime."</font>"; ?></td>
		<td>300</td>
	</tr>
		<td>memory_limit</td>
		<td><? echo "<font color='".$memoryLimitFont."'>".$memoryLimit."</font>"; ?></td>
		<td>256M (minimum)</td>
	</tr>
</table>
</p>

<?php
#####################################################################
#
# Test that gd is loaded
#
#####################################################################
echo "<h3>GD and jpeg library check:</h3>";
echo "<p>";

try
{
	$tester->verifyGdLib();
	echo "GD module loaded with jpeg support.";
} catch( Exception $e ) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "</p>";


#####################################################################
#
# test that ssh2 is installed
#
#####################################################################
echo "<h3>ssh2 check:</h3>";
echo "<p>";

try {
	$tester->verifySSH2();
	echo "SSH2 module loaded. ";
} catch(Exception $e) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "</p>";


#####################################################################
#
# Display an mrc image as png
#
#####################################################################
?>
<h3>Display Images:</h3>
<p><font color='red'>Please confirm that 2 images are visible below.</font> <br />
Don't see them? For more info visit:
<a target='_blank' href='http://emg.nysbc.org/redmine/projects/appion/wiki/Install_Redux_image_server'>[Install the Redux Image Server]</a>
<br />
<br />

<img src='ex1.php' name='MRC test 1'> &nbsp; <img src='ex2.php'
	name='MRC test 2'></p>

<!--  
#####################################################################
#
# Display instructions for running other test scripts 
#
#####################################################################
-->
<h3>Instructions for testing availablity of 3rd party processing packages:</h3>
<p>
Running the following script on the processing server will check that 3rd party processing packages are installed and avaialable from your PATH.
</p>

<p>
<pre>
cd /your_download_area/myami/appion/test<br />
python check3rdPartyPackages.py
</pre>
</p>
<h3>Instructions for running database update scripts:</h3>

<p>
Running the following script will indicate if you need to run any database update scripts.<br />
</p>
<p>
<pre>
cd /your_download_area/myami/dbschema<br />
python schema_update.py
</pre>
</p>

<p>
This will print out a list of commands to paste into a shell which will run database update scripts.<br />
You can re-run schema_update.py at any time to update the list of which scripts still need to be run.<br />
</p>

<!--  
##################################################################### 
# Display other useful information                         
##################################################################### 
-->
<h3>The following PHP extensions are loaded:</h3>
<p><pre>
<?php print_r($modules->listModules()); // List all installed modules ?>
</pre></p>

<?php login_footer(); ?>

</body>
</html>
