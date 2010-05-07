<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$template = new template;
	$template->wizardHeader("Step 2 : Tables Creation Report", DB_INITIALIZATION);
	
	if(file_exists(CONFIG_FILE)){
		require_once(CONFIG_FILE);
		require_once("../inc/leginon.inc");
		require_once("../project/inc/project.inc.php");

		$project = new project();
		$project->install('../xml/projectDBSchema.xml');		
		$leginondata->importTables('../xml/leginonDBSchema.xml');		
		
		// put both databases table in an array $dbTables for display
		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();
		
		$mysqld->select_db(DB_LEGINON, $dbLink);	
		
		$dbTables[DB_LEGINON] = $mysqld->listTables();

		$mysqld->select_db(DB_PROJECT, $dbLink);	
		
		$dbTables[DB_PROJECT] = $mysqld->listTables();
		
	}
	else{
		$has_error[] = "Config file does not exist. Please create it first.";
	}

?>

	<form name='wizard_form' method='POST' action='insertInitData.php'>
		
		<h3>The following tables has been created in both Databases :</h3>
		<p>To insert default data and values in the database tables, please click the "NEXT" button</p>
		
		<input type="submit" value="NEXT" />
		<br /><br />
		
		<table border=0 cellspacing=15 style="font-size: 12px"><tr>
	<?php 
		foreach($dbTables as $key => $tables){
			echo "<td valign=top width='350px'>";
			echo "<h3>'$key' contain the following tables </h3><br />";
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