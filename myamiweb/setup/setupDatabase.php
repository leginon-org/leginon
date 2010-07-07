<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once('../inc/formValidator.php');

	setupUtils::checkSession();
	$update = false;	
	if(!empty($_SESSION['loginCheck'])){
		require_once(CONFIG_FILE);
		$update = true;
	}

	if($_POST){

		$validator = new formValidator();
		
		$validator->addValidation("db_host", $_POST['db_host'], "req");
		$validator->addValidation("db_user", $_POST['db_user'], "req");
		$validator->addValidation("db_leginon", $_POST['db_leginon'], "req");
		$validator->addValidation("db_project", $_POST['db_project'], "req");
		
		$validator->addValidation("db_validate", array( 'host' => $_POST['db_host'], 
														  'username' => $_POST['db_user'],
														  'password' => $_POST['db_pass'],
														  'leginondb' => $_POST['db_leginon'],
														  'projectdb' => $_POST['db_project']), "database");
		
		$validator->runValidation();
		$errMsg = $validator->getErrorMessage();

		
		if(empty($errMsg)){
			
			$_SESSION['post'] = $_POST;
			setupUtils::redirect('setupOthers.php');
			exit();
		}
				
	}	
	
	$template = new template;
	$template->wizardHeader("Step 3 : Setup your MySQL database server parameters", SETUP_CONFIG);
	
?>

	<form name='wizard_form' method='POST' action='<?php echo $_SERVER['PHP_SELF']; ?>'>

	<?php 
		foreach ($_SESSION['post'] as $key => $value){
			$value = trim($value);
			echo "<input type='hidden' name='".$key."' value='".$value."' />";
		}
	?>
		<font>The web tools require one database for Leginon, one database to manage projects,<br />
		and at least one database for Appion. (example : "dbemdata", "project", "ap100")<br />
		Appion requires all three types of database, but Leginon does not require an Appion database<br />
		Please visit <a href="http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database" target="_blank">
		Database setup</a> for more detailed information before you fill in this form.</font><br /><br />
		
		<div id="error"><?php if($errMsg['db_validate']) echo $errMsg['db_validate']."<br /><br />"; ?></div>
		<h3>Enter the Database Host Name:</h3>
		<p>example: localhost, or IP</p>
		<div id="error"><?php if($errMsg['db_host']) echo $errMsg['db_host']; ?></div>
		<input type="text" size=20 name="db_host" 
		<?php 
			if($_POST)
				print("value='".$_POST['db_host']."'");
			else
				($update)? print("value='".DB_HOST."'") : print("value=\"\""); 
		?> /><br /><br />
		<br />
		<h3>Enter the Database username:</h3>
		<p>This is the web database user, it needs to have full access to Leginon and Project databases.<br />
		   It also needs to have the ability to create Appion databases.<br />
		   example: usr_object</p>
		<div id="error"><?php if($errMsg['db_user']) echo $errMsg['db_user']; ?></div>
		<input type="text" size=20 name="db_user" 
		<?php
			if($_POST)
				print("value='".$_POST['db_user']."'");
			else
				($update)? print("value='".DB_USER."'") : print("value=\"\""); 		
		?> /><br /><br />
		<br />
		<h3>Enter the Database password:</h3>
		<p>If no password is required, leave it blank.</p>
		<input type="text" size=20 name="db_pass" <?php ($update)? print("value='".DB_PASS."'") : print("value=\"\""); ?> /><br /><br />
		<br />
		<h3>Enter the Leginon database name:</h3>
		<p>example: leginondb</p>
		<div id="error"><?php if($errMsg['db_leginon']) echo $errMsg['db_leginon']; ?></div>
		<input type="text" size=20 name="db_leginon" 
		<?php 
			if($_POST)
				print("value='".$_POST['db_leginon']."'");
			else
				($update)? print("value='".DB_LEGINON."'") : print("value=\"\"");  		
		?> /><br /><br />
		<br />
		<h3>Enter the Project database name:</h3>
		<p>example: projectdb</p>
		<div id="error"><?php if($errMsg['db_project']) echo $errMsg['db_project']; ?></div>
		<input type="text" size=20 name="db_project" 
		<?php 
			if($_POST)
				print("value='".$_POST['db_project']."'");
			else
				($update)? print("value='".DB_PROJECT."'") : print("value=\"\"");  		
		?> /><br /><br />
		<br />
		
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>