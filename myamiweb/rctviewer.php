<?php
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/cachedb.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require_once "inc/particledata.inc") ? true : false;
}

$sessionId = ($_POST[sessionId]) ? $_POST[sessionId] : $_GET[expId];
$projectId = ($_POST[projectId]) ? $_POST[projectId] : 'all';
$imageId = $_POST[imageId];
$preset = $_POST[$_POST[controlpre]];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

$sessioninfo=$leginondata->getSessionInfo($sessionId);
$session=$sessioninfo['Name'];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();

if(!$sessions)
	$sessions = $leginondata->getSessions('description', $projectId);

if($projectdb) {
	$projects = $projectdata->getProjects('all');
	$sessions=$projectdata->getSessions($sessions);
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
	$sessionId=$sessions[0][id];
if (!$filenames) {
	$filenames = $leginondata->getFilenames($sessionId, $preset);
}
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
$viewer->addjs($jsdata);
$pl_refresh_time="2.0";
$viewer->addPlaybackControl($pl_refresh_time);
$playbackcontrol=$viewer->getPlaybackControl();
$javascript = $viewer->getJavascript();

$view1 = new view('Main View', 'v1');
$view1->setControl();
$view1->setParam('ptclparams',$particleruns);
$view1->setParam('aceruns',$aceruns);
$view1->addMenuItems($playbackcontrol);
$view1->setDataTypes($datatypes);
$view1->setSize(400);
$view1->setPresetScript("getpreset.php?tl=1&vf=0");
$view1->setPresetScript("getpreset.php?tl=1&vf=0");
$view1->setPresetScript('getpreset.php?tl=1&vf=0');
$viewer->add($view1);


$view2 = new view('RCT', 'v3');
$view2->setParam('ptclparams',$particleruns);
$view2->setParam('aceruns',$aceruns);
$view2->setSize(400);
$view2->setDataTypes(array('rct'=>'rct'));
$view2->setPresetScript("getpreset.php?tl=1&vf=0");
$viewer->add($view2);


$javascript .= $viewer->getJavascriptInit();
login_header('image viewer', $javascript, 'initviewer()');
?>&nbsp;
<a class="header" target="summary" href="summary.php?expId=<?php echo $sessionId; ?>">[summary]</a>
<a class="header" target="processing" href="processing/index.php?expId=<?php echo $sessionId; ?>">[processing]</a>
<?php
$viewer->display();
login_footer();
?>
