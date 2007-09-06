<?php
require('inc/leginon.inc');
$username = $_GET['username'];
$imageId = $_GET['imageId'];
$sessionId = $_GET['sessionId'];
$status = "hidden";
$dbc = $leginondata->mysql;
$ret_val = "0";
if ($imageId && $sessionId) {
	if ($_GET['p']=='removed') {
		$q="delete from viewer_pref_image where imageId=$imageId";
		$dbc->SQLQuery($q);
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
