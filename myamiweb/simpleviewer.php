<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/leginon.inc";
require_once "inc/viewer.inc";

// --- Set sessionId
$sessionId=$_POST['sessionId'];
$lastId = $leginondata->getLastSessionId();
$sessionId = (empty($sessionId)) ? $lastId : $sessionId;
$sessions = $leginondata->getSessions('description');

$imageId= $leginondata->getLastFilenameId($sessionId);
$datatypes = $leginondata->getDataTypes($sessionId);

$viewer = new viewer();
$viewer->setSessionId($sessionId);
$viewer->setImageId($imageId);
$viewer->addSessionSelector($sessions);
$javascript = $viewer->getJavascript();

$view1 = new view('Simple Viewer', 'v1');
$view1->setSize(512);
$view1->setDataTypes($datatypes);

$viewer->add($view1);

$javascript .= $viewer->getJavascriptInit();
?>
<html>
<head>
	<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
	<link rel="stylesheet" type="text/css" href="css/view.css">
	<title>Simple Viewer</title>
	<?php echo $javascript; ?>
</head>
<body onload='initviewer();'>
	<?php $viewer->display(); ?>
</body>
</html>
