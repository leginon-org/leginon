<?php
require "inc/auth.php";
$dbemauth = new authlib();
$dbemauth->secret="8ca79c52f2eb411cfb1260b04bd8b605";
$dbemauth->authcook="DBEMAUTH";
$dbemauth->server_url = BASE_URL;
$dbemauth->logout_url = BASE_URL;
?>
