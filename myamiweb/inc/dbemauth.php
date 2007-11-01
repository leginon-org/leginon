<?php
require('inc/auth.php');
$dbemauth = new authlib();
$dbemauth->server="cronus4";
$dbemauth->db_user="usr_project";
$dbemauth->db_pass="";
$dbemauth->database="project";
$dbemauth->secret="8ca79c52f2eb411cfb1260b04bd8b605";
$dbemauth->authcook="DBEMAUTH";
$dbemauth->server_url = "/dbemd";
$dbemauth->logout_url = "/dbemd";
?>
