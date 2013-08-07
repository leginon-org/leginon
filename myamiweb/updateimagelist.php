<?php
require_once "inc/leginon.inc";

// This script is called from js/viewer.js to update image viewer status
// in the database

$imageId = $_GET['imageId'];
$sessionId = $_GET['sessionId'];
$s = $_GET['s'];
switch ($_GET['s']) {
	case "ex":
		$status = "exemplar";
		break;
	case "tr":
		$status = "trash";
		break;
	default:
		$status = "hidden";
}
$preset = $_GET['p'];
$newimage = $leginondata->findImage($imageId, $preset);
$imageId = $newimage['id'];

// check if the preset is the kind that  an action means deleting status only
// undo status assignment (hiding hidden means unhide)
$prefpreset = (in_array($preset, array('exemplar')) || ($preset == 'hidden' && $status == 'hidden')) ? true : false;

$dbc = $leginondata->mysql;
$ret_val = "0";
if ($imageId && $sessionId) {
	// remove old status regardless
	$q="delete from ViewerImageStatus where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);
	// not sure why, but this line repeats the deletion
	$q="delete from `ImageStatusData` where `REF|AcquisitionImageData|image`=$imageId";
	$dbc->SQLQuery($q);

	if ($prefpreset) {
		$ret_val = "1";
	} else {
		// assign new status
		// These include hiding from trash (means move it from trash to hidden)
		$data['REF|AcquisitionImageData|image']=$imageId;
		$data['REF|SessionData|session']=$sessionId;
		$data['status']=$status;
		$table='ViewerImageStatus';
		if ($dbc->SQLInsertIfnotExists($table, $data))
			$ret_val = "1";
	}
}
//returns json object for js usage
header('Content-Type: text/json');
echo "{'value': $ret_val, 'imageId': $imageId }";
?>
