<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">
<title>Leginon Image Viewer</title>
<?
require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');

$sessionId = ($_POST[sessionId]) ? $_POST[sessionId] : $_GET[expId];
$projectId = ($_POST[projectId]) ? $_POST[projectId] : 'all';
$imageId = $_POST[imageId];
$preset = $_POST[$_POST[controlpre]];

// --- Set sessionId
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

// --- Get data type list
$datatypes = $leginondata->getAllDatatypes($sessionId);

$projectdata = new project();
$projects = $projectdata->getProjects('all');

$sessions = $leginondata->getSessions('description', $projectId);
$filenames = $leginondata->getFilenames($sessionId, $preset);

$viewer = new viewer();
$viewer->setProjectId($projectId);
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
//$viewer->addProjectSelector($projects);
$viewer->addFileSelector($filenames);
$viewer->setNbViewPerRow('2');
$javascript = $viewer->getJavascript();

$view1 = new view('View 1', 'v1');
$view1->setDataTypes($datatypes);
$viewer->add($view1);

$view2 = new view('Main View', 'v2');
$view2->setControl();
$view2->setDataTypes($datatypes);
$view2->setSize(512);
$view2->setSpan(2,2);
$viewer->add($view2);

$view3 = new view('View 3', 'v3');
$view3->setDataTypes($datatypes);
$viewer->add($view3);


$javascript .= $viewer->getJavascriptInit();
echo $javascript;
?>
</head>
<body onload='initviewer();'>
<?$viewer->display();?>
</body>
</html>
