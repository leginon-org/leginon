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
	$template->wizardHeader("Step 6 : Review your setup");
	
	$setupUtils = new SetupUtils();
	$setupUtils->copyFiles(CONFIG_TEMPLATE, CONFIG_FILE) or die("Can't copy file");		
	$result = $setupUtils->editConfigFile(CONFIG_FILE, $_POST);
	
	if($result){
		$fileContents = $setupUtils->fileToArray(CONFIG_FILE);
	}

?>

	<form name='wizard_form' method='POST' action='initDBTables.php'>
		
		<h3>Start to build database tables and insert initial variables</h3>
		<p>Web tools require default tables creation in both databases and some initial variables to start.<br />
		If this is your first time setup this web tools, Please click the following button</p>
		&nbsp;&nbsp;<input type="submit" value="Setup initial variables" />
		<br /><br />
		<h3>There is your config file looks like base on your inputs: </h3>
		<p>You can change the values by coming back to this wizard</p>
		
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