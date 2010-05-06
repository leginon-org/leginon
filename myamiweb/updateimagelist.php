<?php
require "inc/leginon.inc";

$imageId = $_GET['REF|AcquisitionImageData|image'];
$sessionId = $_GET['REF|SessionData|session'];
$action = $_GET['ac'];
$status = ($_GET['s']=="ex") ? "exemplar" : "hidden";
$preset = $_GET['p'];
$newimage = $leginondata->findImage($imageId, $preset);
$imageId = $newimage['id'];
$prefpreset = (in_array($preset, array('hidden', 'exemplar'))) ? true : false;
$dbc = $leginondata->mysql;
$ret_val = "0";
if ($imageId && $sessionId) {
	$q="delete from ViewerImageStatus where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);
	$q="delete from `ImageStatusData` where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);
	if ($prefpreset) {
		$ret_val = "1";
	} else {
		$data['REF|AcquisitionImageData|image']=$imageId;
		$data['REF|SessionData|session']=$sessionId;
		$data['status']=$status;
		$table='ViewerImageStatus';
		if ($dbc->SQLInsertIfnotExists($table, $data))
			$ret_val = "1";
	}
}
header('Content-Type: text/json');
echo "{'value': $ret_val, 'imageId': $imageId }";
?>
