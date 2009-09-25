<?php
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
require "inc/cachedb.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require "inc/particledata.inc") ? true : false;
}

$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
$projectId = ($_POST['projectId']) ? $_POST['projectId'] : 'all';
$imageId = ($_POST['imageId']) ? $_POST['imageId'] : $_GET['imageId'];
$preset = $_POST[$_POST['controlpre']];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

$sessioninfo=$leginondata->getSessionInfo($sessionId);
$session=$sessioninfo['Name'];
startcache($session);

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

if ($ptcl) {
	$particle = new particledata();
	$particleruns=$particle->getParticleRunIds($sessionId);
}

// --- update SessionId while a project is selected
$sessionId_exists = $leginondata->sessionIdExists($sessions, $sessionId);
if (!$sessionId_exists) {
	$sessionId=$sessions[0]['id'];
}

$filenames = $leginondata->getFilenames($sessionId, $preset);

// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb) {
	foreach((array)$sessions as $s) {
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
$viewer->addFileSelector($filenames);
$viewer->setNbViewPerRow('2');
$javascript = $viewer->getJavascript();

$view1 = new view('View 1', 'v1');
$view1->setDataTypes($datatypes);
$view1->setParam('ptclparams',$particleruns);
$view1->displayDeqIcon(true);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->setParam('ptclparams',$particleruns);
$view2->setDataTypes($datatypes);
$view2->setSize(512);
$view2->setSpan(2,2);
$view2->displayDeqIcon(true);
$viewer->add($view2);

$view3 = new view('View 3', 'v3');
$view3->setDataTypes($datatypes);
$view3->setParam('ptclparams',$particleruns);
$view3->displayDeqIcon(true);
$viewer->add($view3);


$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
viewer_menu($sessionId);
$viewer->display();
viewer_footer();
?>
