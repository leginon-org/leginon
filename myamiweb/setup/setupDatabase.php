<?php

require_once('template.inc');
require_once('setupUtils.inc');

	setupUtils::checkSession();
	$update = false;	
	if($_SESSION['loginCheck']){
		require_once(CONFIG_FILE);
		$update = true;
	}

	$template = new template;
	$template->wizardHeader("Step 3 : Setup your MySQL database server parameters", SETUP_CONFIG);
	
?>

	<form name='wizard_form' method='POST' action='setupOthers.php'>

	<?php 
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
		<font style="color: red">Web Tools require one database for Leginon, one database to manage projects,<br />
		and at least one database for Appion. (example : "dbemdata", "project", "ap100")<br />
		Appion requires all three types of database, but Leginon does not require an Appion database<br />
		Please visit <a href="http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database" target="_blank">
		Database setup</a> for more detailed information before you fill in this form.</font><br /><br />
		<h3>Enter the Database Host Name:</h3>
		<p>example: "localhost", or IP</p>
		<input type="text" size=20 name="db_host" <?php ($update)? print("value='".DB_HOST."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter the Database username:</h3>
		<p>This is the web database user, it needs to have full access to Leginon and Project databases<br />
		   It also needs to have the ability to create Appion databases.</p>
		<input type="text" size=20 name="db_user" <?php ($update)? print("value='".DB_USER."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter the Database password:</h3>
		<p>If no password is required, leave it blank.</p>
		<input type="text" size=20 name="db_pass" <?php ($update)? print("value='".DB_PASS."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter the Leginon database name:</h3>
		<p>example: "leginondb"</p>
		<input type="text" size=20 name="db_leginon" <?php ($update)? print("value='".DB_LEGINON."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter the Project database name:</h3>
		<p>example: "projectdb"</p>
		<input type="text" size=20 name="db_project" <?php ($update)? print("value='".DB_PROJECT."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>