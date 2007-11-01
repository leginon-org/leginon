<?php
require "inc/viewer.inc";

$redirect = $_REQUEST['ln'];
$login = $dbemauth->login($_POST['username'], $_POST['password']);
if ($login!=2) {
	viewer_header("Login");
	if ($_POST)
		echo "<br>Incorrect Login";
?>
<form method="post" action="<?=$_SERVER['REQUEST_URI']?>" name="">
<table border="0" cellspacing="0" cellpadding="5">
<tr>
	<td>
		<label for="username">Username : </label>
		<input class="field" type="text" value="" name="username" id="username" size="15" >
	</td>
</tr>
<tr> 
	<td>
		<label for="password">Password : </label>
		<input class="field" type="password" name="password"><font size="1">
		<a href="lostpass.php" target="_blank">Lost Password</a>
	</td>
</tr>
<tr> 
        <td width="50%" bgcolor="#FFFFFF"> 
		<input type="submit" value="Login" name="submit">
        </td>
</tr>
</table>
</form>
<?
viewer_footer();
exit;
} else {
	redirect($redirect);
}
?>
