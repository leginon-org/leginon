<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	
	$has_errors = array();
	
	if(file_exists(CONFIG_FILE)){
		require_once(CONFIG_FILE);

		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();

		if($dbLink == false)	$has_errors[] = "Can not connect to Database, Check your db_host, db_usr, and db_password settings.";
		
		else{

			$result = $mysqld->select_db(DB_LEGINON, $dbLink);	

			if($result == false)	$has_errors[] = "Leginon Database does not exist. Please create it first.";
		
			$result = $mysqld->select_db(DB_PROJECT, $dbLink);
			if($result == false)	$has_errors[] = "Project Database does not exist. Please create it first.";	

			// find out is the databases already be initialize 
			$results = $mysqld->getSQLResult('select `key`, value from install where `key` = \'settable\'');
			
			if(empty($has_errors) && (!empty($results))){				
				
				foreach($results as $result){
					$settable = $result['value'];
				}
				
				if($settable){
					setupUtils::redirect('updateDataReport.php');
					exit();
				} 
			}			
		}
	}
	else{
		$has_errors[] = "Config file does not exist. Please create it first.";
	}
	
	$template->wizardHeader("Step 3 : Insert Default Values", DB_INITIALIZATION);

?>

	<form name='wizard_form' method='POST' action='initDataReport.php'>
		
		<h3>Start initial variables setup :</h3>
	<?php if(empty($has_errors)){ ?>
		<p>An administrator account is required.<br />
		   Please fill in the following values.<br /><br />
		   Username: (Can not change the default username)<br /> 
		   <input type="text" size=15 name="username" value="administrator" readOnly style="background:#eeeeee" /><br /><br />
		   Password:<br />
		   <input type="password" size=15 name="password" value="" /><br /><br />
		   Email:<br />
		   <input type="text" size=20 name="email" value="" /><br />

		<p>Please click the "NEXT" button to continue.</p>
		<input type="submit" value="NEXT" />
	<?php } else { ?>
		<br />
		<h3><font color="red">An error occurred!!</font></h3>
		<p>Please solve the following problem before continuing:</p>
	<?php 
			foreach($has_errors as $error){
				echo $error . "<br />";
			}
		} ?>
	</form>
	
<?php 
		
	$template->wizardFooter();
?>