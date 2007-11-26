<?php

require "inc/leginon.inc";

$username = $_GET['username'];
$imageId = $_GET['imageId'];
$sessionId = $_GET['sessionId'];
$action = $_GET['ac'];
$status = ($_GET['s']=="ex") ? "examplar" : "hidden";
$prefpreset = (in_array($_GET['p'], array('hidden', 'examplar'))) ? true : false;
$dbc = $leginondata->mysql;
$ret_val = "0";
if ($imageId && $sessionId) {
	$q="delete from viewer_pref_image where imageId=$imageId";
	$dbc->SQLQuery($q);
	$q="delete from `ImageStatusData` where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);
	if ($prefpreset) {
		echo "1";
		exit;
	}
	//$data['username']=$username;
	$data['imageId']=$imageId;
	$data['sessionId']=$sessionId;
	$data['status']=$status;
	$table='viewer_pref_image';
	if ($dbc->SQLInsertIfnotExists($table, $data))
		$ret_val = "1";
}
echo $ret_val;
?>
