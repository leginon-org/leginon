<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/summarytables.inc";

// --- Set  experimentId
$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

$javascript.= editTextJava();

processing_header("Particle Selection Results", "Particle Selection Results", $javascript, False);

$particle = new particledata();
if ($particle->hasParticleData($expId)) {
	//$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev', 'img');
	$display_keys = array ( 'preset','totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev');
	$selectionruns=$particle->getParticleRunIds($expId);
	foreach ($selectionruns as $selectionrun) {
		//print_r($selectionrun);
		$selectionid = $selectionrun['DEF_id'];
		echo pickingsummarytable($selectionid, true);
	}
} else {
	echo "<font color='#cc3333' size='+2'>No particle information available</font>\n<hr/>\n";
}

processing_footer();
?>
