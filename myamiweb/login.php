<?php
require_once "config.php";
require_once "inc/login.inc";
require_once "inc/formValidator.php";

function dbValidation(){
	// Validate the database connection.
	$validator = new formValidator();
	$validator->addValidation("db_validate", array( 'host' => DB_HOST, 
											  'username' => DB_USER,
											  'password' => DB_PASS,
											  'leginondb' => DB_LEGINON,
											  'projectdb' => DB_PROJECT), "database");
		
	$validator->runValidation();
	return $validator->getErrorMessage();
}

$errMsg = dbValidation();
if(!empty($errMsg)){
	$displayerror = "An error with the database connection has occured. Please <a href='setup/index.php'>check your configuration</a>. ";
}

$username=trim($_POST['username']);
$passwd=trim($_POST['password']);

if(!empty($_POST['anonymous'])){
	$username = 'Anonymous';
}

$login = $dbemauth->login($username, $passwd);
if ($login!=2) {
	login_header("Login",'','',true);
	$displayerror=($_POST) ? "Incorrect Login" : $displayerror;

?>
	<style>
	li {
   		list-style: none; padding:2px;
	}
	</style>
<?php
	if (!file_exists("img/logo.jpg")) {
?>
		<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
		<hr/>
<?php
	} else {
?>
		<div align="center">
		<img src="img/logo.jpg" width="610" height="110">
		</div>
<?php
	}
?>
	<form method="post" action="<?=$_SERVER['REQUEST_URI']?>" name="">
		<center><table cellspacing=20>
			<tr>
			<td align="center">
				<label for="username">Username : </label>
				<input class="field" type="text" value="" name="username" id="username" size="15" >
				<label for="password">Password : </label>
				<input class="field" type="password" name="password" size="15">
				<a class="header" href="lostpass.php" target="_blank">[Lost Password]</a>
			</td>
			</tr>
		<?php if(ENABLE_ANONYMOUS){ ?>
			<tr>
			<td >
				<input type="checkbox" name="anonymous">Login as "Anonymous" for viewing public data sets (Does not required a username and password).</input>
			</td>
			</tr>
		<?php } ?>
			<tr>
			<td align="center">
				<input type="submit" value="Login" name="submit">
				<font size="2">
			</td>
			</tr>
		</table>
		</center>
	</form>
<?php
	if ($displayerror)
		echo '<center><font size="3" color="red">[ '.$displayerror.' ]</font></center>';
	login_footer();
	exit;
} else {

	if (array_key_exists('ln',$_GET)) {
		$redirect_array = array();
		foreach($_GET as $key => $value)
			$redirect_array[] = ($key == 'ln') ? $value:$key.'='.$value;
		$redirect = implode('&',$redirect_array);
	}
	if (!$redirect) $redirect = BASE_URL;

	redirect($redirect);
}
?>
