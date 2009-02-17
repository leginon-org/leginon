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

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET[expId])) ? $lastId : $_GET[expId];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
if ($_GET['showHidden']) $formAction.="&showHidden=True";

$javascript.= editTextJava();

$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo[Name];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();
if($projectdb) {
	$currentproject = $projectdata->getProjectFromSession($sessioninfo['Name']);
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
}

processing_header("Particle Selection Results","Particle Selection Results",$javascript,False);

$inspectcheck=($_POST['onlyinspected']=='on') ? 'CHECKED' : '';
$mselexval=(is_numeric($_POST['mselex'])) ? $_POST['mselex'] 
		: (is_numeric($_GET['mselex']) ? $_GET['mselex'] : false);
echo"<FORM NAME='prtl' method='POST' action='$_SERVER[REQUEST_URI]'>
     <INPUT TYPE='CHECKBOX' name='onlyinspected' $inspectcheck onclick='javascript:document.prtl.submit()'>Don't use particles from discarded images<BR>
     <INPUT CLASS='field' NAME='mselex' TYPE='text' size='5' VALUE='$mselexval'>Minimum correlation value
     </form>\n";
$sessionId=$expId;
$particle = new particledata();
$numinspected=$particle->getNumAssessedImages($sessionId);
echo"Inpected images: $numinspected\n";
if ($particle->hasParticleData($sessionId)) {
	$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev', 'img');
	$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev');
	$particleruns=$particle->getParticleRunIds($sessionId);
	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);
}
else {
        echo "no Particle information available";
}


processing_footer();
?>
