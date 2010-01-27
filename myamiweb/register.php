<?
require "inc/login.inc";

if ($login_check = $dbemauth->is_logged()) {
	header('Location: '.BASE_URL);
}

$register=$error=false;
$displayform=true;

login_header("DBEM Register");
?>
<center><h1>Leginon II Database Tools</h1></center>
<hr/>
<?

if ($_POST) {
	$username=$_POST['username'];
	$password=$_POST['password'];
	$password2=$_POST['password2'];
	$email=$_POST['email'];
	$lastname=$_POST['lastname'];
	$firstname=$_POST['firstname'];
	$register = $dbemauth->register ($username, $password, $password2, $email, $lastname, $firstname);
	echo "regis: $register ";

	if ($register == 2) {
		$displayform=false;
?>
<p>
You have been registered (still pending). We have sent an email to <b>
<?=$email; ?></b> and have recorded the following information :</font>
</p>

  <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#3333FF">
    <tr bgcolor="#FFFFFF">
      <td><font face="Arial, Helvetica, sans-serif" size="2">Name : </font></td>

      <td><font face="Arial, Helvetica, sans-serif" size="2">
        <?php echo $lastname." ".$firstname; ?>
        </font></td>
      </tr>

    <tr bgcolor="#FFFFFF">
      <td><font face="Arial, Helvetica, sans-serif" size="2">Login: </font></td>
      <td><font face="Arial, Helvetica, sans-serif" size="2">
        <?php echo $username; ?>
        </font></td>
		</tr>

    <tr bgcolor="#FFFFFF">
      <td><font face="Arial, Helvetica, sans-serif" size="2">Email : </font></td>
      <td><font face="Arial, Helvetica, sans-serif" size="2">
        <?php echo $email; ?>
        </font></td>
		</tr>

		</table>
<?
	} else {
	$error='
		<p align="center"><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">'
		.$register
		.'</font>'
		.'<br />'
		.'<a class="header" href="lostpass.php" target="_blank">[Lost Password]</a>'
		.'</p>';
	}
}
if ($displayform) {
?>
<form name='register' method='POST' action='register.php'>
<table border="0" cellspacing="0" cellpadding="5">
<tr>
	<td>
		<label for="firstname">Firstname: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$firstname?>" name="firstname" id="firstname" size="15" >
	</td>
	<td>
		<label for="lastname">Lastname: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$lastname?>" name="lastname" id="lastname" size="15" >
	</td>
	</tr>
	<tr>
	<td>
		<label for="email">Email: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$email?>" name="email" id="email">
	</td>
	</tr>
	<tr>
	<td>
		<label for="username">Username: </label>
	</td>
	<td>
		<input class="field" type="text" value="<?=$username?>" name="username" id="username">
	</td>
	</tr>
	<tr>
	<td>
		<label for="password">Password: </label>
	</td>
	<td>
		<input class="field" type="password" value="" name="password" id="password" size="15" >
	</td>
	<td>
		<label for="password2">Confirm: </label>
	</td>
	<td>
		<input class="field" type="password" value="" name="password2" id="password2" size="15" >
	</td>
</tr>
<tr>
	<td colspan="4"><span style="color:#FF0000">!! don't use your TSRI password; https is not enabled !!</span>
	</td>
</tr>
<tr>
<td colspan=2>
	<input class="bt1" type='submit' name='bt_apply' value='Apply'>
</td>
</tr>
</table>
</form>
<?
}
echo $error;
login_footer();
?>
