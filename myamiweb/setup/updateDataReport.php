<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	$template->wizardHeader("DATABASE UPGRADE", DB_INITIALIZATION);
	
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
		
		<h3>Database Update Sucess:</h3>
		<p>Need content.</p>	

<?php 
		
	$template->wizardFooter();
?>
