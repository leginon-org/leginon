<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	$template->wizardHeader("Step 4 : Data Insertion Report");
	
	if(file_exists(CONFIG_FILE)){

		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		$project = new project();
		$project->install('../xml/projectDefaultValues.xml');	

		$leginondata->importTables('../xml/leginonDefaultValues.xml');		
		
		$data = array('username' => $_POST['username'], 
					  'password' => md5($_POST['password']), 
					  'firstname' => 'Admin',
					  'lastname' => 'Admin',
					  'email' => $_POST['email'], 
					  'REF|GroupData|group' => 1);
		
		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();
		
		$mysqld->select_db(DB_LEGINON, $dbLink);	
		
		$mysqld->SQLInsert('UserData', $data);

	}
	else{
		$has_error[] = "Config file does not exist. Please create it first.";
	}

?>
		
		<h3>Data Insertion Sucess:</h3>
		<p>Web tools wizard has successfully insert all the require tables and values to your databases.<br />
		   You can now start using this web tools.<br /><br />
		   If you have enabled the login system, use your administrator's password to login,<br />
		   or you can use register link to create a new user.<br /><br />
           To start using the web tools, please click 
           <a href="http://<?php echo $_SERVER['SERVER_NAME'].BASE_URL; ?>">here</a>.<br /><br />
			Thanks you for using this wizard.</p>	

<?php 
		
	$template->wizardFooter();
?>