<?php
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/cachedb.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require_once "inc/particledata.inc") ? true : false;
}

// --- get Predefined Variables form GET or POST method --- //
list($projectId, $sessionId, $imageId, $preset, $runId) = getPredefinedVars();

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

$sessioninfo=$leginondata->getSessionInfo($sessionId);
$session=$sessioninfo['Name'];

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

$jsdata='';
if ($ptcl) {
	list ($jsdata, $particleruns) = getParticleInfo($sessionId);
	$particle = new particledata();
	$filenames = $particle->getFilenamesFromLabel($runId, $preset);
	$aceruns = $particle-> getCtfRunIds($sessionId);
}

// --- update SessionId while a project is selected
$sessionId_exists = $leginondata->sessionIdExists($sessions, $sessionId);
if (!$sessionId_exists) {
	$sessionId=$sessions[0]['id'];
}

if (!$filenames) {
	$filenames = $leginondata->getFilenames($sessionId, $preset);
}

// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb && !empty($sessions)) {
	foreach($sessions as $k=>$s) {
		if (SAMPLE_TRACK) {
			$tag=$projectdata->getSample(array('Id'=>$s['id'], 'Purpose'=>$s['comment']));
			$tag = ($tag)? " - $tag" : "";
			$sessions[$k]['name'].=$tag;
		}
		if ($s['id']==$sessionId) {
			$sessionname = $s['name_org'];
			// if name need to be modified by sample tag, it should not break
			// breaking is only to save query time
			if (!SAMPLE_TRACK)
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
$viewer->addjs($jsdata);
$javascript = $viewer->getJavascript();

$view1 = new view('View 1', 'v1');
$view1->setDataTypes($datatypes);
$view1->setParam('ptclparams',$particleruns);
$view1->setParam('aceruns',$aceruns);
$view1->displayDeqIcon(true);
$view1->displayDDIcon(true);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->setParam('ptclparams',$particleruns);
$view2->setParam('aceruns',$aceruns);
$view2->setDataTypes($datatypes);
$view2->setSize(512);
$view2->setSpan(2,2);
$view2->displayDeqIcon(true);
$view2->displayDDIcon(true);
$viewer->add($view2);

$view3 = new view('View 3', 'v3');
$view3->setDataTypes($datatypes);
$view3->setParam('ptclparams',$particleruns);
$view3->setParam('aceruns',$aceruns);
$view3->displayDeqIcon(true);
$view3->displayDDIcon(true);
$viewer->add($view3);


$javascript .= $viewer->getJavascriptInit();
login_header('image viewer', $javascript, 'initviewer()');
viewer_menu($sessionId);
$viewer->display();
login_footer();
?>
