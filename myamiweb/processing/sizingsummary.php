<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

// --- Set  experimentId
$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

$javascript.= editTextJava();

processing_header("Object Size/Shape Analysis Results", "Object Size/Shape Analysis Results", $javascript, False);

$particle = new particledata();
if ($particle->hasParticleData($expId)) {
	//$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev', 'img');
	$display_keys = array ( 'preset','total_object_count', 'numimgs', 'min', 'max', 'avg', 'stddev');
	$sizingruns = $particle->getJobProgramRunsInSession ($expId,'contouranalysis');
	foreach ($sizingruns as $sizingrun) {
		//print_r($selectionrun);
		$params = $sizingrun;
		$script_runid = $sizingrun['DEF_id'];
		$run_commands = $particle->getProgramCommands ($script_runid);
		foreach ($run_commands as $command) {
			if ($command['name'] == 'contourid') {
				$params['objectTracing'] = $command['value'];
				break;
			}
		}
		$params['sizingreport'] = $script_runid;
		echo $particle->displayParameters ('Sizing Analysis',$params,array(),$expId);
	}
} else {
	echo "<font color='#cc3333' size='+2'>No particle information available</font>\n<hr/>\n";
}
processing_footer();
?>
