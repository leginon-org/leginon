<?php
require "inc/viewer.inc";

$redirect = $_REQUEST['ln'];
$usern=trim($_POST['username']);
$passwd=trim($_POST['password']);

$login = $dbemauth->login($usern, $passwd);
if ($login!=2) {
	viewer_header("Login");
	$displayerror=($_POST) ? "Incorrect Login" : false;
?>
<style>
li {
   list-style: none; padding:2px;
}
</style>
<center><h1>Leginon II Database Tools</h1></center>
<hr/>
<form method="post" action="<?=$_SERVER['REQUEST_URI']?>" name="">
	<div>
		<ul>
		<li>
		<label for="username">Username : </label>
		<input class="field" type="text" value="" name="username" id="username" size="15" >
		<label for="password">Password : </label>
		<input class="field" type="password" name="password" size="15">
		<a class="header" href="lostpass.php" target="_blank">[Lost Password]</a>
		</li>
		<li>
		<input class="bt1" type="submit" value="Login" name="submit">
		<font size="2">
		</li>
		</ul>
	</div>

</form>
<?
if ($displayerror)
	echo '<center><font size="3" color="red">[ '.$displayerror.' ]</font></center>';
viewer_footer();
exit;
} else {
	if ($usern)
    insertlog($usern, $_SERVER['REMOTE_ADDR'], implode(", ",$_SERVER));

	redirect($redirect);
}
?>
