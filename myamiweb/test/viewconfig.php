<html>
<head>
	<link href="../css/viewer.css" media="all" rel="stylesheet" type="text/css" />
</head>
<body>
<?php
#####################################################################
#
# This file is used to display appion config files in a web browser.
#
#
# There are several hard coded constants in this file that may need to be maintained:
# 1. $configFileLocation - the path to the config.php file
#
#####################################################################
require_once('../config.php');
require_once('../inc/login.inc');
require_once('./inc/webServerTester.inc');
login_header();

// The location of the config file
$configFileLocation = "../config.php";

$tester = new WebServerTester();


echo "<h2>Appion/Leginon Config File</h2>";
echo "Note: Lines with 'user' or 'pass' are not shown.";
echo "<p>";

try {
	$configtext = $tester->printConfig($configFileLocation);
} catch(Exception $e) {
	echo "<font color='red'>".$e->getMessage()."</font>";
}
echo "<pre>";
print_r($configtext);
echo "</pre>";

login_footer(); ?>

</body>
</html>