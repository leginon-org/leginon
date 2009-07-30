<?php
$expId=$_GET['expId'];
require "config_processing.php";
require "inc/session.inc";
setsession();
endsession();
header("location:index.php?expId=$expId");
?>
