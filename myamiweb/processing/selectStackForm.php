<?php
/**
 *      The Leginon software is Copyright 2007
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Create an EMAN Job for submission to a cluster
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

// check if session provided
$expId 	= $_GET['expId'];
$method = $_GET['method'];
$type	= $_GET['type'];

if (!$expId) {
	exit;
}

$particle = new particledata();

// find each stack entry in database
$stackIds = $particle->getStackIds($expId);

// remove stacks with no particles
$filteredStackIds = array();
foreach ($stackIds as $stackId) {
	$numpart = $particle->getNumStackParticles($stackId['stackid']);
	if ($numpart != 0) { 
		$filteredStackIds[] = $stackId['stackid'];
	}
}

?>

<?php processing_header("Appion: Recon Refinement","Select Refinement Stack",$javafunc); ?>

<form name='viewerform' method='POST' ACTION='selectModelForm.php?expId=<?php echo $expId; ?>' >
	<b>Select a stack:</b><br>
	<input type='hidden' name='method' value='<?php echo $method; ?>'>
	<input type='hidden' name='type' value='<?php echo $type; ?>'>
	<P><input type='SUBMIT' NAME='submitstack' VALUE='Use selected stack'>

	<br /><br />
<?php 
	echo "<table class='tableborder' border='1'>\n";
	foreach ($filteredStackIds as $stackId) {
		echo "<tr><td>\n";
		echo "<input type='radio' NAME='stackval' value='$stackId' ";		
		echo ">\n";
		echo "Use<br/>Stack\n";

		echo "</td><td>\n";	
		echo stacksummarytable( $stackId, True, False, False );
		echo "</td></tr>\n";
	}
	echo "</table>\n\n";	
?>
	<P><input type='SUBMIT' NAME='submitstack' VALUE='Use selected stack'>
</form>

<?php echo showReference( $method ); ?>
<?php processing_footer(); ?>
