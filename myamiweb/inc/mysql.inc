<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


class mysql {

	var $hostname;
	var $db_user;
	var $db_pass;
	var $database;
	var $format = "sql";
	var $saveasfile = false;
	var $SQL = array ( 
		'showcolumns'=>1,
		'where'=>" WHERE 1 "
		);
	var $crlf = "\n";

	function mysql ($hostname, $db_user, $dbpass, $database) {
		$this->hostname = $hostname;
		$this->db_user  = $db_user;
		$this->db_pass  = $db_pass;
		$this->database = $database;
	}

	function getDBInfo() {
		return "
			hostname: ".$this->hostname."
			database: ".$this->database."
			user: ".$this->user;
	}

	function connect_db($host="") {
		$host = (empty($host)) ? $this->hostname : $host;
		$link = mysql_connect($host, $this->db_user, $this->db_pass)  or  die( "Unable  to  connect  to  SQL  server");
		if (!link)
			return $this->error[0];
		$db = mysql_select_db($this->database, $link);
		if(!$db)
			return $this->error[1];
		return $link;
	}

	function close_db($resource_link="") {
		if (empty($resource_link))
			mysql_close();
		else
			mysql_close($resource_link);
	}

	function SQLTableExists($name) {
		$table_exists=false;
		$Rtables = $this->SQLQuery("SHOW TABLES");
	    	while($table = mysql_fetch_array($Rtables))
			if ($table[0] == $name) {
				$table_exists=true;
				break;
			}
		return $table_exists;
	}

	function getSQLTableDefinition($table) {

	    $crlf = $this->crlf;
	    $backquotestr='`';
	
	    $schema_create = "";
	
	    $schema_create .= "CREATE TABLE IF NOT EXISTS $table ($crlf";
	
	    $result = $this->SQLQuery("SHOW FIELDS FROM $table") or die("show fields error");
	    while($row = mysql_fetch_array($result))
	    {
	        $schema_create .= "   $backquotestr$row[Field]$backquotestr $row[Type]";
	
	        if(isset($row["Default"]) && (!empty($row["Default"]) || $row["Default"] == "0"))
	            $schema_create .= " DEFAULT '$row[Default]'";
	        if($row["Null"] != "YES")
	            $schema_create .= " NOT NULL";
	        if($row["Extra"] != "")
	            $schema_create .= " $row[Extra]";
	        $schema_create .= ",$crlf";
	    }
	    $schema_create = ereg_replace(",".$crlf."$", "", $schema_create);
	    $result = $this->SQLQuery("SHOW KEYS FROM $table") or die(mysql_error());
	    while($row = mysql_fetch_array($result))
	    {
	        $kname=$row['Key_name'];
	        if(($kname != "PRIMARY") && ($row['Non_unique'] == 0))
	            $kname="UNIQUE|$kname";
	         if(!isset($index[$kname]))
	             $index[$kname] = array();
	         $index[$kname][] = $row['Column_name'];
	    }
	
	    while(list($x, $columns) = @each($index))
	    {
	         $schema_create .= ",$crlf";
	         if($x == "PRIMARY")
	             $schema_create .= "   PRIMARY KEY (" . implode($columns, ", ") . ")";
	         elseif (substr($x,0,6) == "UNIQUE")
	            $schema_create .= "   UNIQUE ".substr($x,7)." (" . implode($columns, ", ") . ")";
	         else
	            $schema_create .= "   KEY $x (" . implode($columns, ", ") . ")";
	    }
	
	    $schema_create .= "$crlf);$crlf";
	    return (stripslashes($schema_create));
	}

	function getSQLTableContent($table, &$content, $where="1") {
	    $crlf = $this->crlf;
	    $local_query = "SELECT * FROM $table WHERE $where";
	    $result = $this->SQLQuery($local_query) or die(mysql_error());
	    $i = 0;
	    while($row = mysql_fetch_row($result))
	    {
	        set_time_limit(60); // HaRa
	        $table_list = "(";
	
	        for($j=0; $j<mysql_num_fields($result);$j++)
	            $table_list .= "`".mysql_field_name($result,$j)."`, ";
	
	        $table_list = substr($table_list,0,-2);
	        $table_list .= ")";
	
	        if(isset($this->SQL["showcolumns"]))
	            $schema_insert = "INSERT INTO $table $table_list VALUES (";
	        else
	            $schema_insert = "INSERT INTO $table VALUES (";
	
	        for($j=0; $j<mysql_num_fields($result);$j++)
	        {
	            if(!isset($row[$j]))
	                $schema_insert .= " NULL,";
	            elseif($row[$j] != "")
	                $schema_insert .= " '".addslashes($row[$j])."',";
	            else
	                $schema_insert .= " '',";
	        }
	        $schema_insert = ereg_replace(",$", "", $schema_insert);
	        $schema_insert .= ")";
	        $content .= trim($schema_insert).";$crlf";
	        $i++;
	    }
	    return (true);
	}

	var $error = array
		(
		"Unable  to  connect  to  SQL  server",
		"Unable  to  select  database"
		);

	function setSQLHost($host) {
		$this->new_sqlhost = $host;
	}

	function getSQLHost() {
		$host = (empty($this->new_sqlhost)) ? $this->hostname : $this->new_sqlhost;
		return $host;
	}

	function SQLQuery($query, $insert=false) {
		$this->connect_db($this->new_sqlhost);
		$result = mysql_query($query) or die("Error: ".mysql_error());
		if ($insert)
			$res = mysql_insert_id();
		else
			$res = $result;
		$this->close_db();
		return $res;
	}

	function SQLQueries($queries) {
		$this->connect_db($this->new_sqlhost);
		$q = (is_array($queries)) ? $queries : array($queries);
		foreach($q as $v)
			mysql_query($v) or die("Error: ".mysql_error());
		$this->close_db();
		return(true);
	}

	function executeSQLInsert($query) {
		$this->connect_db();
		mysql_query($query) or die("Error: ".mysql_error());
		return mysql_insert_id();
		$this->close_db();
		return(true);
	}

}



?>
