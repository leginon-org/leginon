<?php
require_once "config.php";
require_once "inc/login.inc";

$redirect = $_REQUEST['ln'];
$username=trim($_POST['username']);
$passwd=trim($_POST['password']);

if(!empty($_POST['anonmynous'])){
	$username = 'Anonmynous';
}

$login = $dbemauth->login($username, $passwd);
if ($login!=2) {
	login_header("Login");
	$displayerror=($_POST) ? "Incorrect Login" : false;
?>
	<style>
	li {
   		list-style: none; padding:2px;
	}
	</style>
	<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
	<hr/>
	<form method="post" action="<?=$_SERVER['REQUEST_URI']?>" name="">
		<table cellspacing=20>
			<tr>
			<td>
				<label for="username">Username : </label>
				<input class="field" type="text" value="" name="username" id="username" size="15" >
				<label for="password">Password : </label>
				<input class="field" type="password" name="password" size="15">
				<a class="header" href="lostpass.php" target="_blank">[Lost Password]</a>
			</td>
			</tr>
			<tr>
			<td>
				<input type="checkbox" name="anonmynous">Login as "Anonmynous" for viewing public data sets (Does not required a username and password).</input>
			</td>
			</tr>
			<tr>
			<td>
				<input class="bt1" type="submit" value="Login" name="submit">
				<font size="2">
			</td>
			</tr>
		</table>
	</form>
<?php
	if ($displayerror)
		echo '<center><font size="3" color="red">[ '.$displayerror.' ]</font></center>';
	login_footer();
	exit;
} else {
	if ($usern)
    insertlog($usern, $_SERVER['REMOTE_ADDR'], implode(", ",$_SERVER));
	if (!$redirect) $redirect = BASE_URL;
	redirect($redirect);
}
?>
