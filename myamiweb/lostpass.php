<?php
require "inc/login.inc";
login_header("Lost password");
if (!empty($_POST)) {
	
	$lostpass = $dbemauth->lostpwd($_POST['email']);
	$result = "<p>";
	if ($lostpass == 2) {

		$result .= "
			The necessary information has been sent to your email. 
			<br>Please check your email and login.";
		
	} 
	else {
		
		$result .= $lostpass;
		$result .= "<p><input name='back' type='button' value='Try Again' onclick='history.go(-1)' />";
		
	}
	$result .= "</p>";
}
?>
<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
<hr/>
<fieldset>
<form name='register' method='POST' action='<?=$_SERVER['PHP_SELF']?>'>
<table border="0" cellspacing="0" cellpadding="5">
	<?php if(!empty($_POST)) { ?>
	<tr>
		<td><?php echo $result; ?></td>
	</tr>
	<?php } else { ?>
	<tr>
		<td>
			<label for="email">Enter your <b>Username:</b> </label>
		</td>
		<td>
			<input class="field" type="text" value="" name="email" id="email" >
		</td>
	</tr>
	<tr>
		<td>
        	<input class="bt1" type="submit" value="Send Password" name="submit">
		</td>
	</tr>
	<?php } ?>
</table>
</form>
</fieldset>

<?
login_footer();

?>
