<?php 
require_once('template.inc');
require_once('setupUtils.inc');

	session_start();	
	session_destroy();
	
	$template = new template;
	$template->wizardHeader("Welcome : Start configuration of your system", SETUP_CONFIG);
	
	$extensions = get_loaded_extensions();
	
	$required_exts = array('gd' => '\'gd\' module is required for the php mrc module.', 
						   'mrc' => '\'mrc\' module is required for displaying mrc images.', 
						   'mysql' => '\'mysql\' module is required for connecting to the mysql database.', 
						   'mysqli' => '\'mysqli\' module is required for connecting to the mysql database.', 
						   'ssh2' => '\'ssh2\' module is required for connecting to the processing host or cluster.');
	
	$phpModulesMessages = array();
	
	foreach($required_exts as $ext => $desc){
		
		if(!in_array($ext, $extensions))
			$phpModulesMessages[] = $desc;
	}

	$fileExist = setupUtils::checkFile(CONFIG_FILE);
	
	if($_POST){
		
		session_start();

		$_SESSION['time'] = time();
		
		if($_POST['newSetup']){
				// setup session for new config file setup.
			$_SESSION['newSetup'] = true;

			setupUtils::redirect('setupBase.php');		
			exit;
		}
		else{
			require_once(CONFIG_FILE);
			// if username and password match
			// create session
			// redirect to setupBase page.
			if($_POST['username'] == DB_USER && $_POST['password'] == DB_PASS){
				//if username and password match.

				$_SESSION['loginCheck'] = true;
				// redirect to setupBase.
				
				setupUtils::redirect('setupBase.php');
				exit;
			} else {
				$errorMessage = "The username and password you provided are incorrect. Enter again...";
			
				// destroy the session because error.
				session_destroy();
			}
		}
		
	}

?>
	<h3>Start here to setup and configure the web tools configuration file.</h3>
	<p>Please follow each step.</p>
	
	<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
<?php 
	if($fileExist){
?>
		<p>An existing configuration file has been detected.<br />
		Please enter the <b>"Database Username and Password"</b> for verification.<br />
		If you forgot your username and password, it can be found in config.php in the myamiweb folder.</p>

		<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
		<?php if(!empty($errorMessage)) echo"<font color='red'><p>$errorMessage</p></font>"; ?>
		<h3>Enter the Database username:</h3>
		<input type="text" size=20 name="username" value="" /><br /><br />
		<h3>Enter the Database password:</h3>
		<input type="password" size=20 name="password" value="" /><br /><br />
	
<?php 
	}
	else{
		
		echo "<p>This wizard will take you step by step through the process of 
		         setting up the Appion web tools config file.<br /><br />";
		echo "Please use <font color='red'>alphanumeric characters</font> in your entries. 
				Special characters may not be used. For security reasons, there is a 30 minute time limit for each page. 
				If you exceed this limit, you will be returned to this page.<br /><br />";
		
		if(!empty($phpModulesMessages)){
			echo "There are some php module(s) missing. Please install the missing module(s) before you start.<br />
				  For more information please check <a target='_blank' href='http://ami.scripps.edu/redmine/projects/appion/wiki/Download_additional_Software_(CentOS_Specific)'>
				  Install Complete list of additional packages</a>.<br /><br />";
			foreach($phpModulesMessages as $message)
				echo $message . '<br />';
		}
		echo "<br />";
		echo "When you are ready to start please click on the \"NEXT\" button.</p><br />";
		echo "<input type='hidden' name='newSetup' value=true />";
 		
	}
?>
	<input type="submit" value="NEXT" />
	</form>

<?php 
	$template->wizardFooter();
?>