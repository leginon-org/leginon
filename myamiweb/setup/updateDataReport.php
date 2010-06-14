<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;

	
	if(file_exists(CONFIG_FILE)){

		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		$leginondata->importTables('../xml/leginonUpdateValues.xml');		
		$project = new project();
		$project->install('../xml/projectUpdateValues.xml');	

	}
	else{
		$has_error[] = "Config file does not exist. Please create it first.";
	}

	$template->wizardHeader("Database Upgrade to v1.7", DB_INITIALIZATION);

?>
		
		<h3>Database Update Successful:</h3>
		<p>All required data has been successfully inserted into the databases. <br ></br><font color="red">You are not done yet</font>.</p>
		<p>You need to run three python scripts (schema-r12857.py, schema-r13713.py and chema-r14077.py) under your downloaded "myami-2.0/dbschema"
		   in order to complete the upgrade process.</p>
		   
		<p>For more details visit 
		<a target="_blank" href="http://ami.scripps.edu/redmine/projects/leginon/wiki/How_to_Update_from_v16_%28Linux%29">upgrade manual</a>.</p>	
		<p>You can visit the web tools <a href="http://<?php echo $_SERVER['SERVER_NAME'].BASE_URL; ?>">here</a> after you complete all the upgrade process.</p>
<?php 
		
	$template->wizardFooter();
?>
