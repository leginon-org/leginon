<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";

$refreshtime = ($_POST['refreshtime']) ? $_POST['refreshtime'] : 10;

// --- Set sessionId
$sessionId=$_POST[sessionId];
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;
// --- Get last imageId from the current session
$imageId= $leginondata->getLastFilenameId($sessionId);

// --- Get data type list
$datatypes = $leginondata->getDatatypes($sessionId);

$sessions = $leginondata->getSessions('description');

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if(!$sessions) {
	$sessions = $leginondata->getSessions('description', $projectId);
}

if($projectdb) {
	$projects = $projectdata->getProjects('all');
	$sessionexists = $projectdata->sessionExists($projectId, $sessionId);
	if (!$sessionexists) {
		$sessionId = $sessions[0]['id'];
	}
}

$viewer = new viewer();
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
$viewer->addLoiControl($refreshtime);
$viewer->addCommentBox();
$viewer->addQueueCountBox();

$javascript = $viewer->getJavascript();

$v=1;
foreach ($datatypes as $datatype) {
	$name = "v$v";
	$title= "View $v";
	$view = new view($title, $name);
	$view->displayDeqIcon(true);
	$view->setDataTypes($datatypes);
	$view->selectDataType($datatype);
	$viewer->add($view);
	$v++;
}

$javascript .= $viewer->getJavascriptInit();
login_header('Leginon Observer Interface', $javascript, 'initviewer()');
?>
<a class="header" target="summary" href="summary.php?expId=<?php echo $sessionId; ?>">[summary]</a>
<a class="header" target="processing" href="processing/index.php?expId=<?php echo $sessionId; ?>">[processing]</a>
<?php
$viewer->display();
login_footer();
?>
