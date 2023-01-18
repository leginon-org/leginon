<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";

$refreshtime = ($_POST['refreshtime']) ? $_POST['refreshtime'] : 60;

// --- get Predefined Variables form GET or POST method --- //
list($projectId, $sessionId, $imageId, $preset, $runId, $scopeId) = getPredefinedVars();

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;
// --- Get last imageId from the current session
$imageId= $leginondata->getLastFilenameId($sessionId);

$scopes = $leginondata->getScopesForSelection();
$scopeId = (empty($scopeId)) ? false:$scopeId;

// --- Get data type list
$datatypes = $leginondata->getDataTypes($sessionId);

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

$sessions = $leginondata->getSessions('description', $projectId, '', $scopeId);

if($projectdb) {
	$projects = $projectdata->getProjects('all');
	$sessionexists = $projectdata->sessionExists($projectId, $sessionId);
	if (!$sessionexists) {
		$sessionId = $sessions[0]['id'];
	}
}

if ( is_numeric(SESSION_LIMIT) && count($sessions) > SESSION_LIMIT) $sessions=array_slice($sessions,0,SESSION_LIMIT);

// --- Get is_auto
$is_auto = $leginondata->getIsAutoSession($sessionId);

$viewer = new viewer();
if($projectdb && !empty($sessions)) {
	foreach($sessions as $k=>$s) {
		if ($s['id']==$sessionId) {
			$sessionname = $s['name_org'];
			break;
		}
	}
	$currentproject = $projectdata->getProjectFromSession($sessionname);
	$viewer->setProjectId($projectId);
	$viewer->addProjectSelector($projects, $currentproject);
}

$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
$viewer->setScopeId($scopeId);
$viewer->addScopeSelector($scopes);
$viewer->addAutoSessionLabel($is_auto);
$viewer->addLoiControl($refreshtime);
$viewer->addCommentBox();
$viewer->addQueueCountBox();

$javascript = $viewer->getJavascript();

# commenting out the image display since nobody seems to need it anymore
if (defined('SHOW_LOI_VIEWS') && SHOW_LOI_VIEWS == true) {
	$v=1;
	foreach ($datatypes as $datatype) {
		$name = "v$v";
		$title= "View $v";
		$view = new view($title, $name);
		$view->displayDeqIcon(true);
		$view->setDataTypes($datatypes);
		$view->selectDataType($datatype);
		$view->setCacheOnly(false);
		$viewer->add($view);
		$v++;
	}
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
