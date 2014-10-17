<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	
	if(file_exists(CONFIG_FILE)){
		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$project = new project();
		
		$dbLink = $mysqld->connect_db();
		$mysqld->select_db(DB_PROJECT, $dbLink);	
		
		// for new install
		$project->install('../xml/projectDBSchema.xml');
		$leginondata->importTables('../xml/leginonDBSchema.xml');
			
		// put both databases table in an array $dbTables for display
		// need to reconnect again, because SQLQuery function close the db connection.
		$dbLink = $mysqld->connect_db();
		
		$mysqld->select_db(DB_PROJECT, $dbLink);	
		$dbTables[DB_PROJECT] = $mysqld->listTables();
				
		$mysqld->select_db(DB_LEGINON, $dbLink);	
		
		$dbTables[DB_LEGINON] = $mysqld->listTables();

		
	}
	else{
		$has_error[] = "The configuration file does not exist. Please create it first.";
	}
	
	$template->wizardHeader(" Table Creation", DB_INITIALIZATION);

?>

	<form name='wizard_form' method='POST' action='insertInitData.php'>
		
		<h3>The following tables have been created in the Databases when this page is loaded :</h3>
		
		<br /><br />
		
		<table border=0 cellspacing=15 style="font-size: 12px"><tr>
	<?php 
		foreach($dbTables as $key => $tables){
			echo "<td valign=top width='350px'>";
			echo "<h3>'$key' contains the following tables </h3><br />";
			foreach($tables as $table){
				echo"$table <br/>";
			}
			echo"</td>";
		}	
		
	?>
		</tr>
		</table>
		
	</form>
	
<?php 
		
	$template->wizardFooter();
?>
