<?php
$expId=$_GET['expId'];
require "inc/session.inc";
setsession();
endsession();
header("location:processing.php?expId=$expId");
?>
