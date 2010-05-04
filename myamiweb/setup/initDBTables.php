<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	$template->wizardHeader("Step 1 : Create Web Tools Default Tables");
	
	$has_errors = array();
	
	if(file_exists(CONFIG_FILE)){
		require_once(CONFIG_FILE);

		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();

		if($dbLink == false)	$has_errors[] = "Can not connect to Database, Check your db_host, db_usr, and db_password.";
		
		else{

			$result = $mysqld->select_db(DB_LEGINON, $dbLink);	

			if($result == false)	$has_errors[] = "Leginon Database (".DB_LEGINON.") does not exist. Please create it first.";
		
			$result = $mysqld->select_db(DB_PROJECT, $dbLink);
			if($result == false)	$has_errors[] = "Project Database (".DB_PROJECT.") does not exist. Please create it first.";	
		}
	}
	else{
		$has_error[] = "Config file does not exist. Please create it first.";
	}

?>

	<form name='wizard_form' method='POST' action='initTablesReport.php'>
		
		<h3>Start initial variables setup :</h3>
		<p>Web tools requires some initial tables and variables to start<br />
		This is required for new databases setup.</p>
	<?php if(empty($has_errors)){ ?>
		<p>System has been checked your datbase connection to both databases<br /><br />
		<?php echo DB_LEGINON . " is ready to import !<br /> ";
			  echo DB_PROJECT . " is ready to import !<br />"; ?><br /> 
		Please click the "NEXT" button to craete tables for both databases.</p>
		<input type="submit" value="NEXT" />
	<?php } else { ?>
		<br />
		<h3><font color="red">Error occur !!</font></h3>
		<p>Please solved the following problem before you can move on:</p>
	<?php 
			foreach($has_errors as $error){
				echo $error . "<br />";
			}
		} ?>
	</form>
	
<?php 
		
	$template->wizardFooter();
?>