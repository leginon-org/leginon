<?php

require_once('template.inc');
require_once('setupUtils.inc');
require_once("../inc/mysql.inc");

	$dbNotExistSolution = "Solution:<br />
							1.  You might have entered the wrong database name in your config.php file.<br /> 
							    You can go back to the <a href='index.php'>setup wizard</a> and edit the database name.<br /><br />
							2.  You have not created this database on your mysql server.<br />You have 
								to create this database before database initialization.<br /><br />
							3.  The database username does not have access privilege to this 
								database. You need to make sure this database user has certain 
								access privileges to the database. Please visit 
								<a href='http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database' 
								target='_blank'>Database setup</a> for more detailed information.<br />";
	
	$dbConnectionSolution = "Solution:<br />
							 1.	You might have entered the wrong database hostname, username or password.<br />&nbsp;&nbsp;&nbsp;&nbsp;
							    You can go back to the <a href='index.php'>setup wizard</a> to edit this information.<br /><br />
							 2.	Your database server is not running.<br />&nbsp;&nbsp;&nbsp;&nbsp;
							 	Please visit <a href='http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database' 
								target='_blank'>Database setup</a> for more detailed information.<br /><br />
							 3.	Your database server is not using standard port number 3306.<br />&nbsp;&nbsp;&nbsp;&nbsp;
							    If your database is using a different port, please follow the following example for setting up your host name.<br />&nbsp;&nbsp;&nbsp;&nbsp;
							    Syntax: dbhost.school.edu:portnumber<br /> &nbsp;&nbsp;&nbsp;&nbsp;
							    Example: test.school.edu:3308<br /> <br />
							 4.	If your web server and database server are on different machines,<br />&nbsp;&nbsp;&nbsp;&nbsp;
							 	please make sure there is no firewall between the web server and the database server.<br /><br />
							 5.	Please make sure the database server's user is allowed to connect from the web host.<br />&nbsp;&nbsp;&nbsp;&nbsp;
							    Please visit <a href='http://ami.scripps.edu/redmine/projects/appion/wiki/Setup_MySQL_database' 
								target='_blank'>Database setup</a> for more detailed information.<br />";
	$confNotExistSolution = "Solution:<br />
							 There is no config.php in your myamiweb directory<br />
							 Please go to the <a href='index.php'>setup wizard</a> to create config.php file.<br />";
	
	$template = new template;
	$template->wizardHeader("Step 1 : Database Tables Creation", DB_INITIALIZATION);
	
	$has_errors = array();
	
	if(file_exists(CONFIG_FILE)){
		require_once(CONFIG_FILE);

		$mysqld = new mysql(DB_HOST, DB_USER, DB_PASS);
		$dbLink = $mysqld->connect_db();

		if($dbLink == false)	$has_errors[] = "Cannot connect to the database server with the following information:<br />
												 db_host : ".DB_HOST."<br />
												 db_usr : ".DB_USER."<br /><br />".$dbConnectionSolution;
		
		else{

			$result = $mysqld->select_db(DB_LEGINON, $dbLink);	

			if($result == false)	$has_errors[] = "\"".DB_LEGINON."\" database does not exist.<br /><br />".$dbNotExistSolution;
		
			$result = $mysqld->select_db(DB_PROJECT, $dbLink);
			if($result == false)	$has_errors[] = "\"".DB_PROJECT."\" database does not exist.<br /><br />".$dbNotExistSolution;	
		
			// find out is the databases already be initialize 
			$results = $mysqld->getSQLResult('select `key`, value from install where `key` = \'version\'');
			if(empty($has_errors) && (!empty($results))){				
				
				foreach($results as $result){
					$currentDBVersion = $result['value'];
				}
				
				if(!empty($currentDBVersion)) $has_errors[] = $msg = 'You do not need to do anything.';
			}
			$mysqld->close_db($dbLink);
		}
	}
	else{
		$has_errors[] = "config.php file does not exist.<br /><br />".$confNotExistSolution;
	}

?>
	<form name='wizard_form' method='POST' action='initTablesReport.php'>
		
		<h3>Start initial variables setup :</h3>
		<p>Web tools requires default tables and variables.</p>
		<p><font color="red">This is required for new and upgrade databases Only. </font><?php echo $msg; ?></p>
		
	<?php if(empty($has_errors) && (empty($msg))){ ?>
		<p>The system has checked your connection to both databases<br /><br />
		<?php echo DB_LEGINON . " is ready to import !<br /> ";
			  echo DB_PROJECT . " is ready to import !<br />"; ?><br /> 
		Please click the "NEXT" button to create tables for both databases.</p>
		<input type="submit" value="NEXT" />
	<?php } elseif(empty($msg)) { ?>
		<br />
		<h3><font color="red">Error(s) have occured !</font></h3>
		<p>Please solve the following problem then click "Try Again":</p>
		<form>
			<input type="button" value="Try Again" onClick="location.href='<?php echo $PHP_SELF; ?>'">
		</form>
		<br />
	<?php 
			foreach($has_errors as $error){
				echo "<p>".$error . "</p>";
			}
		} else {?>

		<p>Tables creation and initialization have been done in both your databases (<?php echo DB_LEGINON.', '.DB_PROJECT; ?>) 
		<p>Your current database schema is in version <?php echo $currentDBVersion; ?>.</p>
		<p>To run the wizard again, please click <a href="index.php">here</a>.<br />
		   To run the web tools, please click <a href="http://<?php echo $_SERVER['SERVER_NAME'].BASE_URL; ?>">here</a>. </p>
	<?php } ?>
	</form>
	
<?php 
		
	$template->wizardFooter();
?>