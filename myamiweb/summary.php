<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/project.inc";

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET['expId'])) ? $lastId : $_GET['expId'];
$numimages = $leginondata->getNumImages($expId);

if ($numimages > 8000 ) {
	redirect(BASE_URL.'summary_links.php?expId='.$expId);
} else {
	redirect(BASE_URL.'summary_full.php?expId='.$expId);
}
?>
	
