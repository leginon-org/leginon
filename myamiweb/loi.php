<?
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require ('inc/leginon.inc');
require ('inc/viewer.inc');

$refreshtime = $_POST[refreshtime];

// --- Set sessionId
$sessionId=$_POST[sessionId];
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;

// --- Get last imageId from the current session
$imageId= $leginondata->getLastFilenameId($sessionId);

// --- Get data type list
$datatypes = $leginondata->getDatatypes($sessionId);

$sessions = $leginondata->getSessions('description');

$viewer = new viewer();
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
$viewer->addLoiControl($refreshtime);

$javascript = $viewer->getJavascript();

$v=1;
foreach ($datatypes as $datatype) {
	$name = "v$v";
	$title= "View $v";
	$view = new view($title, $name);
	$view->setDataTypes($datatypes);
	$view->selectDataType($datatype);
	$viewer->add($view);
	$v++;
}

$javascript .= $viewer->getJavascriptInit();
?>
<html>
<head>
	<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
	<link rel="stylesheet" type="text/css" href="css/view.css">
	<title>Leginon Observer Interface</title>
	<?=$javascript;?>
</head>
<body onload='init();'>
	<?$viewer->display();?>
</body>
</html>
