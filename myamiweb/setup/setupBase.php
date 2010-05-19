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
	$template->wizardHeader("Step 1: Define web tools base variables", SETUP_CONFIG);
	
	$utils = new setupUtils();
	$utils->setBasePath($_SERVER['PHP_SELF']);
	
?>

	<form name='wizard_form' method='POST' action='setupEmail.php'>
		<input type="hidden" name="project_name" value="<?php echo PROJECT_NAME; ?>" />
		<input type="hidden" name="base_path" value="<?php echo $utils->basePath; ?>" />
		<input type="hidden" name="base_url" value="<?php echo $utils->baseURL; ?>" />
		<input type="hidden" name="project_url" value=<?php echo $utils->projectURL; ?> />
		
		<h3>Enter a title for your Appion and Leginon tools web pages:</h3><br />
		<p>This title will appear on all the tools web pages.</p>	
		<p>example: Appion and Leginon DB Tools</p><br />
		<input type="text" size=50 name="project_title" value="<?php ($update) ? print(PROJECT_TITLE) : print("Appion and Leginon DB Tools"); ?>" /><br /><br />
		<br />
		<h3>We have automatically setup these values for your web server.</h3>
		<p>Ignore these unless there is an error.</p>
		<p>Base_PATH : <?php echo $utils->basePath; ?></p>
		<p>BASE_URL : <?php echo $utils->baseURL; ?></p>
		<p>PROJECT_URL : <?php echo $utils->projectURL; ?></p>
		<br />
		<input type="submit" value="NEXT" />
	</form>
	
<?php 
		
	$template->wizardFooter();
?>
