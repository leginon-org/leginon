<?php
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require_once "inc/particledata.inc") ? true : false;
}

// --- get Predefined Variables form GET or POST method --- //
list($projectId, $sessionId, $imageId, $preset, $runId) = getPredefinedVars();

// --- set 2nd view's preset
$presetv1 = ($_POST) ? $_POST['v1pre'] : $_GET['v1pre'];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

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
if (!$sessionId_exists)
	$sessionId=$sessions[0]['id'];
if (!$filenames) {
	$filenames = $leginondata->getFilenames($sessionId, $preset);
}
// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb) {
	foreach((array)$sessions as $k=>$s) {
		if (SAMPLE_TRACK) {
			$tag=$projectdata->getSample(array('Id'=>$s['id'], 'Purpose'=>$s['comment']));
			$tag = ($tag)? " - $tag" : "";
			$sessions[$k]['name'].=$tag;
		}
		if ($s['id']==$sessionId) {
			$sessionname = $s['name_org'];
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
$pl_refresh_time=".5";
$viewer->addPlaybackControl($pl_refresh_time);
$playbackcontrol=$viewer->getPlaybackControl();
$javascript = $viewer->getJavascript();

$view1 = new view('View 1', 'v1');
$view1->setDataTypes($datatypes);
$view1->selectDataType($presetv1);
$view1->setParam('ptclparams',$particleruns);
$view1->setParam('aceruns',$aceruns);
$view1->displayDDIcon(true);
$view1->setSize(512);
$view1->displayTag(true);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->displayTag(true);
$view2->setParam('ptclparams',$particleruns);
$view2->setParam('aceruns',$aceruns);
$view2->displayDDIcon(true);
$view2->setDataTypes($datatypes);
$view2->selectDataType($preset);
$view2->addMenuItems($playbackcontrol);
$view2->setSize(512);
$view2->setSpan(2,2);
$viewer->add($view2);


$javascript .= $viewer->getJavascriptInit();
login_header('image viewer', $javascript, 'initviewer()');
viewer_menu($sessionId);
$viewer->display();
login_footer();
?>
