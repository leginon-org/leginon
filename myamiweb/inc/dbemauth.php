<?php
require('inc/auth.php');
$dbemauth = new authlib();
$dbemauth->server="";
$dbemauth->db_user="";
$dbemauth->db_pass="";
$dbemauth->database="";
$dbemauth->secret="8ca79c52f2eb411cfb1260b04bd8b605";
$dbemauth->authcook="DBEMAUTH";
$dbemauth->server_url = "/";
$dbemauth->logout_url = "/";
?>
