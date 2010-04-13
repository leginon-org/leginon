<?php

require_once('template.inc');
require_once('setupUtils.inc');

	$template = new template;
	$template->wizardHeader("Step 3 : Setup your MySQL database server parameters");
	
?>

	<form name='wizard_form' method='POST' action='setupOthers.php'>

	<?php 
		foreach ($_POST as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
		//echo "<input type='hidden' name='gp_user' value='users' />";
		echo "<input type='hidden' name='def_processing_prefix' value='ap' />";
	?>
		<font style="color: red">Web Tools require one database for Leginon, one database for manage all your projects,<br />
		and at least one database for Appion. (example : "dbemdata", "project", "ap100")<br />
		Appion require all three types of database, but Leginon does not require ap database<br />
		Please visit <a href="http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database" target="_blank">
		Database setup</a> for more detail information before you fill in this form.</font><br /><br />
		<h3>Enter the Database Host Name:</h3>
		<p>example: "localhost", or IP</p>
		<input type="text" size=20 name="db_host" value="" /><br /><br />
		<br />
		<h3>Enter the Database username:</h3>
		<p>This is the web database user, it needs to have full access to Leginon and Project databases<br />
		   It also needs to have the ability to create Appion databases.</p>
		<input type="text" size=20 name="db_user" value="" /><br /><br />
		<br />
		<h3>Enter the Database password:</h3>
		<p>If no password required, leave it blank.</p>
		<input type="text" size=20 name="db_pass" value="" /><br /><br />
		<br />
		<h3>Enter the Leginon database name:</h3>
		<p>example: "leginondb"</p>
		<input type="text" size=20 name="db_leginon" value="" /><br /><br />
		<br />
		<h3>Enter the Project database name:</h3>
		<p>example: "projectdb"</p>
		<input type="text" size=20 name="db_project" value="" /><br /><br />
		<br />
		<h3>Enter Appion database prefix:</h3>
		<p>We recommend to use 'ap' as Appion database prefix.</p>
		<input type="text" size=5 name="def_processing_prefix" value="ap" /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>