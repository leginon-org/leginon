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
	$fileContents = $setupUtils->editConfigFile(CONFIG_TEMPLATE, $_POST);

	$copyResult = $setupUtils->copyFiles(CONFIG_TEMPLATE, CONFIG_FILE);

	if($copyResult){
			$result = $setupUtils->arrayToFile(CONFIG_FILE, $fileContents);

		if($result)
			$fileContents = $setupUtils->fileToArray(CONFIG_FILE);
	}
	else{

		$cpErrorMsg = "Apache User does not have permission to create configure file.<br />
				You can change your \"myamiweb\" folder's permission or <br />
				you can use the code below and create a config.php under the myamiweb folder.";

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