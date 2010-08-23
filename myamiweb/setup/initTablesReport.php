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
		
		// query out the settable value, so we can find out the user already have database schema or not.
		// we might also need to check the version number for feature update, but not this release.
		
		$results = $mysqld->SQLQuery('select `key`, value from install where `key` = \'settable\'');

		if(($results != false) && mysql_num_rows($results) > 0){				
			// for upgrade			
			$results = $mysqld->SQLQuery('describe processingdb');
			$project->install('../xml/projectUpdateSchema.xml');	
			if (($results == false) || mysql_num_rows($results) == 0) {
				$project->install('../xml/projectProcessingAddonSchema.xml');	
			}
		}
		else{
			// for new install
			$project->install('../xml/projectDBSchema.xml');
			$leginondata->importTables('../xml/leginonDBSchema.xml');
		}
			
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
	
	$template->wizardHeader("Step 2 : Tables Creation Report", DB_INITIALIZATION);

?>

	<form name='wizard_form' method='POST' action='insertInitData.php'>
		
		<h3>The following tables have been created in the Databases :</h3>
		<p>To insert default data and values in the database tables, please click the "NEXT" button.</p>
		
		<input type="submit" value="NEXT" />
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
