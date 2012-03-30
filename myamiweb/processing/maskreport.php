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

// --- Set  experimentId
$expId = $_GET['expId'];

processing_header('Mask Creation Results','Mask Creation Results');

echo"<table border='0' cellpadding=10>
<TR><td>\n";

$particle = new particledata();
if ($particle->hasMaskMakerData($expId)) {
	$display_keys = array ( 'totregions', 'numimgs', 'areamean', 'Imean', 'Istddev', 'img');
	$maskruns=$particle->getMaskMakerRunIds($expId);
	echo $particle->displayMaskRegionStats($expId,$maskruns, $display_keys, $inspectcheck);
} else {
	echo "no Mask information available";
}

echo "</td></tr></table>\n";

processing_footer();

?>
