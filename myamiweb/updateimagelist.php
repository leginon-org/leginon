<?php
require "inc/leginon.inc";

$username = $_GET['username'];
$imageId = $_GET['imageId'];
$sessionId = $_GET['sessionId'];
$action = $_GET['ac'];
$status = ($_GET['s']=="ex") ? "exemplar" : "hidden";
$preset = $_GET['p'];
$newimage = $leginondata->findImage($imageId, $preset);
$imageId = $newimage['id'];
$prefpreset = (in_array($preset, array('hidden', 'exemplar'))) ? true : false;
$dbc = $leginondata->mysql;
$ret_val = "0";
if ($imageId && $sessionId) {
	$q="delete from viewer_pref_image where imageId=$imageId";
	$dbc->SQLQuery($q);
	$q="delete from `ImageStatusData` where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);
	if ($prefpreset) {
		$ret_val = "1";
	} else {
		//$data['username']=$username;
		$data['imageId']=$imageId;
		$data['sessionId']=$sessionId;
		$data['status']=$status;
		$table='viewer_pref_image';
		if ($dbc->SQLInsertIfnotExists($table, $data))
			$ret_val = "1";
	}
}
header('Content-Type: text/json');
echo "{'value': $ret_val, 'imageId': $imageId }";
?>
