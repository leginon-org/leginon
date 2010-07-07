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
		$validator->addValidation("project_title", $_POST['project_title'], "req");
		$validator->addValidation("project_title", $_POST['project_title'], "alpha_s");
		$validator->runValidation();
		$errMsg = $validator->getErrorMessage();
		
		if(empty($errMsg)){
			
			$_SESSION['post'] = $_POST;
			setupUtils::redirect('setupEmail.php');
			exit();
		}	
		
	}
	
	$template = new template;
	
	$utils = new setupUtils();
	$utils->setBasePath($_SERVER['PHP_SELF']);
	
	$template->wizardHeader("Step 1: Define web tools base variables", SETUP_CONFIG);
	
?>

	<!-- <form name='wizard_form' method='POST' action='setupEmail.php'> -->
	<form name='wizard_form' method='POST' action='<?php echo $_SERVER['PHP_SELF']; ?>'>
	
		<input type="hidden" name="project_name" value="<?php echo PROJECT_NAME; ?>" />
		<input type="hidden" name="base_path" value="<?php echo $utils->basePath; ?>" />
		<input type="hidden" name="base_url" value="<?php echo $utils->baseURL; ?>" />
		<input type="hidden" name="project_url" value=<?php echo $utils->projectURL; ?> />
		
		<h3>Enter a title for your Appion and Leginon tools web pages:</h3><br />
		<p>This title will appear on all the tools web pages.</p>	
		<p>example: Appion and Leginon DB Tools</p><br />

		<div id="error"><?php if($errMsg['project_title']) echo $errMsg['project_title']; ?></div>
		
		<input type="text" size=50 name="project_title" value="
			<?php 	if($_POST){ 
						print($_POST['project_title']); 
					}else{ 
						if($update) print(PROJECT_TITLE); else print("Appion and Leginon DB Tools");
					} 
			?>" /><br /><br />
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
