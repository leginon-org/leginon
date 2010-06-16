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

	$setupUtils = new SetupUtils();
	
	// Builds the config file from the template with the users input and stores in an array 
	$fileContents = $setupUtils->editConfigFile(CONFIG_TEMPLATE, $_POST);

	// Check to see if the apache user has permission to write to the Myami web 
	// directory and copys the template to the file location 
	// (config.php.template to config.php)
	$copyResult = $setupUtils->copyFiles(CONFIG_TEMPLATE, CONFIG_FILE);

	// If the user has write access, copy array contents to file
	if($copyResult){
			$result = $setupUtils->arrayToFile(CONFIG_FILE, $fileContents);

		// If the copy succeded, store the config file to the array to display the actual
		// contents of config.php to the user.
		if($result)
			$fileContents = $setupUtils->fileToArray(CONFIG_FILE);
	}
	else{

		$cpErrorMsg = "Apache User does not have permission to create the configuration file.<br />
				You can change your \"myamiweb\" folder's permission or <br />
				you can use the code below and create a config.php under the myamiweb folder.";

        }
        
	$template->wizardHeader("Step 6 : Review your setup", SETUP_CONFIG);

?>

	<form name='wizard_form' method='POST' action='initDBTables.php'>

		<h3>Initialize database tables</h3>
		<p>The Appion and Leginon Web Tools require default tables to be created in both databases.<br />
		   Please click the following button for first-time setup or upgrade from older versions only:</p>
		&nbsp;&nbsp;<input type="submit" value="DB Initialization" />
		<br /><br />
		<h3>This is what your config file looks like based on the settings you provided: </h3>
		<p>You can change the settings later by returning to this <a href="index.php">wizard</a>.</p>
		<?php if(!empty($cpErrorMsg)) echo "<p><font color='red'>".$cpErrorMsg."</font></p>"; ?>
		<p>
	<?php
		foreach ($fileContents as $eachLineOfFile){
                    if(trim($eachLineOfFile) == "<?php") echo "&lt;?php <br />";
                    else echo $eachLineOfFile . "<br />";
		}

	?>
		</p>
	</form>

<?php

	$template->wizardFooter();
?>