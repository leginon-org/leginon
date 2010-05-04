<?php 
require_once('template.inc');
require_once('setupUtils.inc');

	session_start();	
	session_destroy();
	
	$template = new template;
	$template->wizardHeader("Welcome : Start setup your config file");
	
	$fileExist = setupUtils::checkFile(CONFIG_FILE);
	
	if($_POST){
		session_start();

		$_SESSION['time'] = time();
		
		if($_POST['newSetup']){
				// setup session for new config file setup.
			$_SESSION['newSetup'] = true;

			header("Location: setupBase.php");			
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
				header("Location: setupBase.php");
				exit;
			} else {
				$errorMessage = "Your username and password do not match. Enter again...";
			
				// destroy the session because error.
				session_destroy();
			}
		}
		
	}

?>
	<h3>There is where you start to setup and configure the web tools config file.</h3>
	<p>Please follow each step.</p>
	
	<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
<?php 
	if($fileExist){
?>
		<p>We have detected there is already a config file setup in the system<br />
		Please enter the <b>"Database username and Password"</b> for verification<br />
		If you forget your username and password, it is in your config.php under myamiweb forder.</p>

		<form name='wizard_form' method='POST' action='<?php echo $PHP_SELF; ?>'>
		<?php if(!empty($errorMessage)) echo"<font color='red'><p>$errorMessage</p></font>"; ?>
		<h3>Enter the Database username:</h3>
		<input type="text" size=20 name="username" value="" /><br /><br />
		<h3>Enter the Database password:</h3>
		<input type="password" size=20 name="password" value="" /><br /><br />
	
<?php 
	}
	else{
		
		echo"<p>This wizard will asks you few questions about.....<br />";
		echo"To Start it, please click the \"NEXT\" button.</p>";
		echo"<input type='hidden' name='newSetup' value=true />";
 		
	}
?>
	<input type="submit" value="NEXT" />
	</form>

<?php 
	$template->wizardFooter();
?>