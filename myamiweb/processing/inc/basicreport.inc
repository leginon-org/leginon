<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
// This file contains the SQL and html required to display a basic report page based on 
// the database table name provided to the class. For more information see:
// http://emg.nysbc.org/redmine/projects/appion/wiki/Using_basicReportinc
//--------------------------------------------------------------------------------------


// if the config file does not exist, redirect to setup wizard.
if( !file_exists(dirname(__FILE__).'/../../config.php') ){

	$location = 'location:'.substr($_SERVER['REQUEST_URI'], 0, -11).'setup/index.php';
	header($location);
	exit();
}

require_once dirname(__FILE__).'/../../config.php';
require_once "inc/mysql.inc";

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";

class BasicReport {

	function __construct( $expId, $jobtype, $runDataTableName=NULL, $thisExpIdOnly=false ) {
		$this->expId 	  = $expId;
		$this->jobtype 	  = $jobtype;
		$this->thisExpIdOnly 	  = $thisExpIdOnly;
		$this->tableCount = 0;  // used to ensure recursive table display methods do not run indefinatly.
		$this->MAX_TABLES = 30;	// the max number of sub-tables that will display before cutting off display recursion.	
		$this->allDisplayKeys = array();
		$this->allDisplayKeys['DEF_id'] = 1; //trick to supress this field from showing in non-verbose reports
		$this->mysql 	  = new mysql(
							DB_HOST,
							DB_USER,
							DB_PASS,
							PARTICLE_DB);
							
		if ($runDataTableName) $this->setTableName( $runDataTableName );
	}

	//--------------------------------------------------------------------------------------
	// Set a table name that is specific to the data you wish to display.
	// $runDataTableName - often holds information about runnames, paths and 
	//  links to parameter tables.
	//--------------------------------------------------------------------------------------
	function setTableName( $runDataTableName ) {
		if ( $this->mysql->SQLTableExists($runDataTableName) ) {
			$this->runDataTableName = $runDataTableName;
		} else {
			$dbinfo = $this->mysql->getDBInfo();
			throw new Exception("The table named $runDataTableName could not be found with $dbinfo" );
		}
	}
	
	//--------------------------------------------------------------------------------------
	//--------------------------------------------------------------------------------------
	// General database functions that can be used for any table
	//--------------------------------------------------------------------------------------
	//--------------------------------------------------------------------------------------
	 
	function getTableDataByDefId( $tablename, $defId ) {
		$q = "select * from `$tablename` "
			." where `DEF_id` = '$defId' ";
		list($r) = $this->mysql->getSQLResult($q);
		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			throw new Exception("Database Error with Table: $tablename, defId: $defId DB error: $dberror ");
		}
		
		return $r;
	} 
	
	//--------------------------------------------------------------------------------------
	// This generic function takes a DB tablename and column name
	// and returns all rows that contain the string matching the $pattern
	// in the provided column. The pattern only needs to be a substring
	// of the field entry to match.
	//--------------------------------------------------------------------------------------
	function getAllEntriesLike( $tablename, $columnname, $pattern ) {
		$q = "select * "
			."from `$tablename` "
			."where $columnname like '%$pattern%' "
			."order by DEF_id asc";
		$r = $this->mysql->getSQLResult($q);
		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			throw new Exception("Database Error with Table: $tablename, finding $columnname entries like $pattern. DB error: $dberror ");
		}
		return $r;
	}

	//--------------------------------------------------------------------------------------
	// This will take any table that includes a reference to 
	// the ApAppionJobData table and return the AppionJobData row
	// corresponding to the table and DEF_id provided. 
	// ApAppionJobData includes an entry for every job started for this session.
	// It provides status information as well as job name, type and path.  
	//--------------------------------------------------------------------------------------
	function getAppionJobData( $tablename, $defId ) {
		$q = "SELECT j.* "
			."FROM `$tablename` AS t "
			."LEFT JOIN `ApAppionJobData` AS j "
			." ON (t.`REF|ApAppionJobData|job` = j.`DEF_id`) "			
			."WHERE t.`DEF_id` = $defId";
		list($r) = $this->mysql->getSQLResult($q);
		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			throw new Exception("Database Error with Table: $tablename, defId: $defId looking for a reference to apAppionJobData. DB error: $dberror ");
		}
		return $r;
	}
	
	//--------------------------------------------------------------------------------------
	//-----------------------------------------------------------
	// Functions specific to the provided runData table ($this->runDataTableName)
	//-----------------------------------------------------------
	//--------------------------------------------------------------------------------------
	
	function hasRunData() {
		return ($this->getLastRunId()) ? true : false;	
	}
	
	function getRunData( $runId ) {
		return $this->getTableDataByDefId( $this->runDataTableName, $runId );
	}	
	
	function getLastRunId() {
		$q = "select DEF_id as runId "
			."from `$this->runDataTableName` "
			."order by DEF_id desc limit 1";
		list($r) = $this->mysql->getSQLResult($q);
		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			throw new Exception("Database Error with Table: $this->runDataTableName, while looking for the last run entry. DB error: $dberror ");
		}
		return $r['runId'];
	}

	function getRunDatas( $showHidden=False ) {
		$q = "SELECT r.* "
			."FROM `$this->runDataTableName` AS r ";
		$q.= "WHERE 1 ";
		if (!$showHidden) $q.= " AND (r.`hidden` IS NULL OR r.`hidden` = 0) ";
		if ($this->thisExpIdOnly) $q.= "AND r.`REF|leginondata|SessionData|session`=$this->expId ";
		$q.= "ORDER BY r.`DEF_id` DESC ";
		$r = $this->mysql->getSQLResult($q);
		if ( $r === False ) {
			$dberror = $this->mysql->getError();
			throw new Exception("Failed to find run data with Table: $this->runDataTableName,  DB error: $dberror ");
		}
		return $r;
	}	
	
	
	//--------------------------------------------------------------------------------------
	//--------------------------------------------------------------------------------------
	// Display functions
	// The following functions do not require the run table to be set.
	// These are used for displaying information to the user.
	//--------------------------------------------------------------------------------------
	//--------------------------------------------------------------------------------------
	
	
	//--------------------------------------------------------------------------------------
	// displaySummaryTable() is the primary function to be used from another php page.
	// It creates a standard appion header box for the data, then calls fillHtmlTable()
	// to format the data into rows and colums that will appear under the header.
	// 
	// $rundata - key value pairs from a databse table row. Should include the 'DEF_id' and 'runname' or 'name'.
	// $showSubTables - if true, any tables that are referenced by
	//                  the $runData provided will also be displayed to the user recursively.
	// $runReportLink - defines the URL path that should be used if the user wants to display more detailed 
	//					information about the run. ex. 'testsuiterunreport.php?expId='.$expId.'&rId='.$runData['DEF_id']
	// $verbose - set to True to show every field of every table. For simple reports, Set to False to show each field once, 
	//				removing repeats like DEF_timestamp.
	// Returns - A string with the HTML code to display the run data in a table with an appion formatted header
	//--------------------------------------------------------------------------------------
	function displaySummaryTable( $runData, $runReportLink, $showSubTables=False, $verbose=True )
	{
		// Don't display hidden entries
		//if ( $runData['hidden'] == 1 ) return "";
		
		// reset the subtable count - prevents tradgedy if tables have circular references
		$this->tableCount = 0;
		
		// Set values to display to user
		$jobtype = $this->jobtype;
		$runId = $runData['DEF_id'];
		
		// Set the run name. Too bad our DB is not standardized...
		// TODO: consider adding $runname to input params
		if ($runData['name']) {
			$runname = $runData['name'];
		} else if ($runData['runname']) {
			$runname = $runData['runname'];
		} else if ($runData['stackRunName']) {
			$runname = $runData['stackRunName'];
		}
		
		// Format the heading bar for display
		$j = "$jobtype Info: <span class='aptitle' >"
			."<a href='$runReportLink'>"
			.$runname."</a></span> (ID: $runId)\n";
	
		$selectiontable.= apdivtitle($j);
		
		// if we are returning a streamlined table, add the table tag at this level rather than recursivly below.
		if ( !$verbose ) {
			$selectiontable.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
		}
		$selectiontable.= $this->fillHtmlTable($runData,"", $showSubTables, $verbose);
		// if we are returning a streamlined table, add the table tag at this level rather than recursivly below.
		if ( !$verbose ) {
			$selectiontable.= "</table>\n";
		}
		
		return $selectiontable;
	}
	
	//--------------------------------------------------------------------------------------
	// Creates the HTML for a table based on an array of key value pairs. The Keys are 
	// displayed down the first column of the table, and the corresponding values fill in 
	// the second column. 
	//
	// $keyedData - an array of key value pairs, such as a row from a databse
	// $title - Opional title to display with the table
	// $showSubTables - If true, any keys in the format "REF|databse|tablename|field" will
	//                  be used to display databse entries from related tables.
	// Returns - the html for the table as a string 
	//--------------------------------------------------------------------------------------
	function fillHtmlTable( $keyedData, $title="", $showSubTables=False, $verbose=True )
	{
		if ($verbose) {
			// Create the title and border of the table
			$table = "<h4>".$title."</h4>";
			$table.= "<table class='tableborder' border='1' cellspacing='1' cellpadding='2'>\n";
		}
			
		// Parse the column names of the DB table. If it is a reference to another table
		// and $showSubTables is set, build the display code for the referenced table.
		// If it is not a reference, add the column name and value to $display_keys
		// to be formatted as an html row later.
		foreach ($keyedData as $key=>$value) {
			if (substr($key, 0, 4) == "REF|" ) {
				if (substr($key, 0, 16) == "REF|leginondata|") {
					list($ref, $database, $tablename, $field) = explode("|", $key);
				} else {
					list($ref, $tablename, $field) = explode("|", $key);
				}

				if ( $value && $showSubTables ) {
					// Add the html formatted sub table to a list to display it after closing out the current table html tag. 
					$subtableList[] = $this->displayTable( $tablename, $value, $key, $showSubTables, $verbose);
				}
			} else {
				if ( $value ) $display_keys[$key] = $value;
			}
		}
		
		// Format all the column names and values as rows in an html table.
		foreach($display_keys as $k=>$v) {
			// if we want to display all keys, even repeats, or we have not displayed this key yet, print it
			if ( $verbose || !isset($this->allDisplayKeys[$k]) ) {
				$table.= formatHtmlRow($k,$v);
				$this->allDisplayKeys[$k] = $v;
			}
		}
		
		if ( $verbose ) {
			// Close out the html table tag
			$table.= "</table>\n";
			$table.= "<p>\n";
		}

		// Finally, add any sub-tables to our html code.
		if ($subtableList) {
			foreach ($subtableList as $i => $subtable) {
				$table.= $subtable;
			}
		}		
		
		return $table;
	}
	
	//--------------------------------------------------------------------------------------
	// Given a tablename and defID, this will create the HTML table describing the database table row.
	// 
	// $tablename - the name of the database table to extract data from
	// $defId - the defId value used to lookup data in the table
	// $title - optional title to display with the table
	// $showSubTables - if True, any tables that are referenced by this table will also be displayed.
	// Returns - A String containing the HTML code to display the database information in a table(s)
	//
	// Note: theoretically, the DB could be defined in a way that two tables reference each other.
	//	This situation could lead to this recursive method going on indefinatly. To avoid this, 
	//	there is a MAX_TABLES value that will halt everything if too many tables have been created.
	//--------------------------------------------------------------------------------------
	function displayTable( $tablename, $defId, $title="" , $showSubTables=False, $verbose=True)
	{
		// not sure if the DB has any circular references...
		// Fail gracefully.
		$this->tableCount++;
		if ($this->tableCount > $this->MAX_TABLES ) {
			return "Hiding tables because too many have been displayed. There could be a circular reference in the Database.";
		}
		
		// Pull the data from the database
		$tableRow = $this->getTableDataByDefId($tablename, $defId);
		
		// Create the HTML to display the data
		$formattedTable = "";
		if ( $tableRow ) {
			$formattedTable = $this->fillHtmlTable( $tableRow , $title, $showSubTables, $verbose);
		}
		return $formattedTable;
	}
}
	
?>
