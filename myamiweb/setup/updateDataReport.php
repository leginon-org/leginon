<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	$template->wizardHeader("Database Upgrade to v2.0", DB_INITIALIZATION);
	
	if(file_exists(CONFIG_FILE)){

		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		// please uncomment the following two lines after we done the content. //
		//$project = new project();
		//$project->install('../xml/projectUpdateValues.xml');	

	}
	else{
		$has_error[] = "Config file does not exist. Please create it first.";
	}

?>
		
		<h3>Database Update Successful:</h3>
		<p>Wizard has successfully insert all require data into your databases. But you are not done yet.<br />
		   You also need to run two python scripts (schema-r12857.py and chema-r13713.py) under "Leginon2.0/dbschema" folder
		   in order to complete the whole upgrade process.</p>
		   
		<p>For more detail information please visit upgrade manual  
		<a href="http://ami.scripps.edu/redmine/projects/leginon/wiki/How_to_Update_from_v16_%28Linux%29">here</a>.</p>	

<?php 
		
	$template->wizardFooter();
?>
