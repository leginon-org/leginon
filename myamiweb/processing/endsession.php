<?php
$expId=$_GET['expId'];
require "../config.php";
require "inc/session.inc";
setsession();
endsession();
header("location:index.php?expId=$expId");
?>
