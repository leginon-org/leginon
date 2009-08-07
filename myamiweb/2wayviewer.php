<?php
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require "inc/particledata.inc") ? true : false;
}

$sessionId = ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
$projectId = ($_POST['projectId']) ? $_POST['projectId'] : 'all';
$imageId = ($_POST['imageId']) ? $_POST['imageId'] : $_GET['imageId'];
$preset = ($_POST) ? $_POST[$_POST['controlpre']] : $_GET['pre'];
$presetv1 = ($_POST) ? $_POST['v1pre'] : $_GET['v1pre'];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if($projectdb)
	$projects = $projectdata->getProjects('all');

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);

if ($ptcl) {
	$particle = new particledata();
	$particleruns=$particle->getParticleRunIds($sessionId);
}

// --- update SessionId while a project is selected
$sessionId_exists = $leginondata->sessionIdExists($sessions, $sessionId);
if (!$sessionId_exists)
	$sessionId=$sessions[0]['id'];
$filenames = $leginondata->getFilenames($sessionId, $preset);
// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb) {
	foreach((array)$sessions as $k=>$s) {
		$tag=$projectdata->getSample(array('Name'=>$s['name_org'], 'Purpose'=>$s['Purpose']));
		$tag = ($tag)? " - $tag" : "";
		$sessions[$k]['name'].=$tag;
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
$view1->setSize(512);
$view1->displayTag(true);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->displayTag(true);
$view2->setParam('ptclparams',$particleruns);
$view2->setDataTypes($datatypes);
$view2->selectDataType($preset);
$view2->addMenuItems($playbackcontrol);
$view2->setSize(512);
$view2->setSpan(2,2);
$viewer->add($view2);


$javascript .= $viewer->getJavascriptInit();
viewer_header('image viewer', $javascript, 'initviewer()');
viewer_menu($sessionId);
$viewer->display();
viewer_footer();
?>
