<?php
/*
 * This script is going to create project database and 
 * leginon database.
 * Then create all the required tables and insert all the 
 * default values. 
 * 
 * example to run this script in:
 * php initialDBsetup.php -L leginondb -P projectdb -H localhost -U root -S password -E erichou@scripps.edu
 */


require_once("../myamiweb/inc/mysql.inc");
require_once("../myamiweb/inc/xmlapplicationimport.inc");

// get required arguments
/*
 * L: - DB_LEGINON
 * P: - DB_PROJECT
 * H: - DB_HOST
 * U: - DB_USER
 * S: - DB_PASS
 * E: - administrator email address
 */
$options = getopt("L:P:H:U:S:E:");
// only password 'S' is optional
if(empty($options['L']) || empty($options['P']) || empty($options['H']) || empty($options['U']) || empty($options['E'])) {
	print "Missing Required Arguments";
	exit();
}

if(empty($options['S']))
	$options['S'] == '';
	
define('DB_HOST', $options['H']);
define('DB_USER', $options['U']);
define('DB_PASS', $options['S']);
define('DB_PROJECT', $options['P']);
define('DB_LEGINON', $options['L']);
define('PROJECT_DB_SCHEMA', '../myamiweb/xml/projectDBSchema.xml');
define('PROJECT_DEFAULT_VALUE', '../myamiweb/xml/projectDefaultValues.xml');
define('LEGINON_DB_SCHEMA', '../myamiweb/xml/leginonDBSchema.xml');
define('LEGINON_DEFAULT_VALUE', '../myamiweb/xml/leginonDefaultValues.xml');

class projectDBImport{
	
	var $mysql;

	function projectDBImport() {
		$this->mysql = new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
		if (!$this->mysql->checkDBConnection())
			echo $this->mysql->dbError();
	}

	// This install function is for setup wizard.
	function install($defaultProjectSchema) {
		
		$app = new XMLApplicationImport($defaultProjectSchema);
		$sqldef = $app->getSQLDefinitionQueries();
		$fieldtypes = $app->getFieldTypes();
		if ($this->mysql->checkDBConnection())
			$this->mysql->SQLAlterTables($sqldef, $fieldtypes);
		$sqldata = $app->getSQLDataQueries();
		//--- insert data;
		foreach ((array)$sqldata as $table=>$queries) {
			foreach($queries as $query) {

					$this->mysql->SQLQuery($query,true);
			}
		}
	}
}

class leginonDBImport{
	
	var $mysql;
	
	function leginonDBImport() {
		$this->mysql = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
		if (!$this->mysql->checkDBConnection())
			echo $this->mysql->dbError();
	}
	
	function importTables($filename) {
		$app = new XMLApplicationImport($filename);
		$sqldef = $app->getSQLDefinitionQueries();
		$sqldata = $app->getSQLDataQueries();
		$fieldtypes = $app->getFieldTypes();
		if ($this->mysql->checkDBConnection()) {
			$this->mysql->SQLAlterTables($sqldef, $fieldtypes);
			foreach ((array)$sqldata as $table=>$queries) {
				foreach($queries as $query) {
					eval("\$sqlinsert= \"".addslashes($query)."\";");
						$this->mysql->SQLQuery($sqlinsert,true);
				}
			}
		}
		return true;
	}	
	
	function leginonDBinsert($table, $keyValuePairs){
		$this->mysql->SQLInsert($table, $keyValuePairs);
	}
}

$link = mysql_connect(DB_HOST, DB_USER, DB_PASS);
if(!$link) {
	die('Could not connect: ' . mysql_error());
}	
mysql_query('create database '. DB_PROJECT, $link);
mysql_query('create database '. DB_LEGINON, $link);
mysql_close($$link);
	
$projectDBImport = new projectDBImport(DB_PROJECT);	
$projectDBImport->install(PROJECT_DB_SCHEMA);
$projectDBImport->install(PROJECT_DEFAULT_VALUE);

$leginonDBImport = new leginonDBImport(DB_LEGINON);
$leginonDBImport->importTables(LEGINON_DB_SCHEMA);
$leginonDBImport->importTables(LEGINON_DEFAULT_VALUE);

$adminAccount = array('username' => 'administrator', 
			  'password' => md5('administrator'), 
			  'firstname' => 'Appion-Leginon',
			  'lastname' => 'Administrator',
			  'email' => $option['E'], 
			  'REF|GroupData|group' => 1);

$anonymousAccount = array('username' => 'Anonymous', 
			  'password' => md5('anonymous'), 
			  'firstname' => 'Anonymous',
			  'lastname' => 'Anonymous',
			  'email' => $option['E'], 
			  'REF|GroupData|group' => 4);

$leginonDBImport->leginonDBinsert('UserData', $adminAccount);
$leginonDBImport->leginonDBinsert('UserData', $anonymousAccount);

print "Databases setup successfully ! \n";

?>