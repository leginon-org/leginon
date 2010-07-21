<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	
	if(file_exists(CONFIG_FILE)){

		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		$project = new project();
		$project->install('../xml/projectDefaultValues.xml');	

		$leginondata->importTables('../xml/leginonDefaultValues.xml');		
		
		$adminAccount = array('username' => $_POST['username'], 
					  'password' => md5($_POST['password']), 
					  'firstname' => 'Appion-Leginon',
					  'lastname' => 'Administrator',
					  'email' => $_POST['email'], 
					  'REF|GroupData|group' => 1);
		
		$anonymousAccount = array('username' => 'Anonymous', 
					  'password' => md5('anonymous'), 
					  'firstname' => 'Anonymous',
					  'lastname' => 'Anonymous',
					  'email' => $_POST['email'], 
					  'REF|GroupData|group' => 4);
		
		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();
		
		$mysqld->select_db(DB_LEGINON, $dbLink);	
		
		$mysqld->SQLInsert('UserData', $adminAccount);
		$mysqld->SQLInsert('UserData', $anonymousAccount);
		# insert leginon settings default
		require_once("../inc/setdefault.php");
	}
	else{
		$has_error[] = "The configuration file does not exist. Please create it first.";
	}

	$template->wizardHeader("Step 4 : Data Insertion Report", DB_INITIALIZATION);

?>
		
		<h3>Data Insertion Success:</h3>
		<p>Web tools wizard has successfully inserted all the required tables and values to your databases.<br />
		   You can now start using the Appion and Leginon web tools.<br /><br />
		   If you have enabled the login system, use your administrator's password to login.<br />
           To start using the web tools, please click 
           <a href="http://<?php echo $_SERVER['SERVER_NAME'].BASE_URL; ?>">here</a>.<br /><br />
           To go back to the wizard, please click <a href="index.php">here</a><br /><br />
		</p>	

<?php 
		
	$template->wizardFooter();
?>
