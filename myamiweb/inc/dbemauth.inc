<?php
require_once "inc/auth.php";
$dbemauth = new authlib();
if (defined('COOKIE_PASSPHRASE') && COOKIE_PASSPHRASE !='') {
	$dbemauth->secret=md5(COOKIE_PASSPHRASE);
} else {
	$dbemauth->secret="8ca79c52f2eb411cfb1260b04bd8b605";
}
$dbemauth->authcook="DBEMAUTH";
$dbemauth->server_url = BASE_URL;
$dbemauth->logout_url = BASE_URL;
?>
