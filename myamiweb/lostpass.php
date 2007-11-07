<?php
require "inc/viewer.inc";
viewer_header("Lost password");
if ($_POST) {
	$lostpass = $dbemauth->lostpwd($_POST['email']);

	if ($lostpass == 2) {
	echo "<p>";
	echo '
	The necessary information been sent to your email 
	please check your email and login.
	';
	echo "</p>";
	} else {
		echo "<p>";
		echo $_POST['email']." not found in database";
		echo "</p>";
	}
} else {
?>
<center><h1>Leginon II Database Tools</h1></center>
<hr/>
<form name='register' method='POST' action='<?=$_SERVER['PHP_SELF']?>'>
<fieldset>
<table border="0" cellspacing="0" cellpadding="5">
<tr>
	<td>
		<label for="email">Email <b>or</b> Username: </label>
	</td>
	<td>
		<input class="field" type="text" value="" name="email" id="email" >
	</td>
</tr>
<tr>
	<td>
          <input class="bt1" type="submit" value="Find Password" name="submit">
	</td>
</tr>
</table>
</fieldset>
</form>
<?
viewer_footer();
}
?>
