<?php

require_once('template.inc');
require_once('setupUtils.inc');

	session_start();
	session_destroy();

		// if no post variable, redirect back to index page
	if(empty($_POST)){
		header("Location: index.php");
		exit();
	}
	
	$template = new template;
	$template->wizardHeader("Step 6 : Review your setup", SETUP_CONFIG);
	
	$setupUtils = new SetupUtils();
	$setupUtils->copyFiles(CONFIG_TEMPLATE, CONFIG_FILE) or die("Can't copy file");		
	$result = $setupUtils->editConfigFile(CONFIG_FILE, $_POST);
	
	if($result){
		$fileContents = $setupUtils->fileToArray(CONFIG_FILE);
	}

?>

	<form name='wizard_form' method='POST' action='initDBTables.php'>
		
		<h3>Initializing database table</h3>
		<p>Web tools require default tables to be created in both databases.<br />
		   If this is your first time setting up these web tools, please click the following button:</p>
		&nbsp;&nbsp;<input type="submit" value="DB Initialization" />
		<br /><br />
		<h3>This is what your config file looks like based on the settings you provided: </h3>
		<p>You can change the settings later by returning to this <a href="index.php">wizard</a></p>
		
		<p>
	<?php 
		foreach ($fileContents as $eachLineOfFile){
			echo $eachLineOfFile . "<br />";
		}
	
	?>
		</p>
	</form>
	
<?php 
		
	$template->wizardFooter();
?>