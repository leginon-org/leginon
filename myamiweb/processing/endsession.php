<?php
$expId=$_GET['expId'];
$projectId=$_GET['projectId'];
require_once "../config.php";
require_once "inc/session.inc";
setsession();
endsession();
if (!empty($expId))
	header("location:index.php?expId=$expId");
else
	// handle upload image to new session special case
	header("location:index.php?projectId=$projectId");
?>
