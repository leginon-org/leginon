<?php
require "inc/leginon.inc";
require "inc/viewer.inc";
require "inc/project.inc";
$ptcl = (@require "inc/particledata.inc") ? true : false;

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
	$defaultrunId=$particleruns[0]['DEF_id'];
	foreach ($particleruns as $p) {
		$runId=$p['DEF_id'];
		list($selectionparams)=$particle->getSelectionParams($runId);
		$diam = $selectionparams['diam'];
		$correlationstats=$particle->getStats($runId);
		$correlationstats['diam']=$diam;
		$particleruns[$k]['diam']=$diam;
		$data[$runId]=$correlationstats;
	}
}

// --- update SessionId while a project is selected
$sessionId_exists = $leginondata->sessionIdExists($sessions, $sessionId);
if (!$sessionId_exists)
	$sessionId=$sessions[0][id];
$filenames = $leginondata->getFilenames($sessionId, $preset);
// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$viewer = new viewer();
if($projectdb) {
	foreach($sessions as $k=>$s) {
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
?>
<a class="header" target="summary" href="summary.php?expId=<?php echo $sessionId; ?>">[summary]</A>
<a class="header" target="processing" href="processing/index.php?expId=<?php echo $sessionId; ?>">[processing]</A>
<a class="header" target="make jpgs" href="processing/runJpgMaker.php?expId=<?php echo $sessionId; ?>">[make jpgs]</A>
<?php
$viewer->display();
viewer_footer();
?>
