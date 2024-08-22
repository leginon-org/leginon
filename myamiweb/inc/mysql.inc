<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */


class mysql {

	var $db_host;
	var $db_user;
	var $db_pass;
	var $db_link;
	var $db;
	var $sqldefault = array();
	var $sqlquery;
	var $SQL = array ( 
		'showcolumns'=>1,
		'where'=>" WHERE 1 "
		);
	var $crlf = "\n";
	private  $__SQLQuery_link;

	function __construct ($db_host, $db_user, $db_pass, $db=null) {
		$this->db_host	= $db_host;
		$this->db_user	= $db_user;
		$this->db_pass	= $db_pass;
		$this->db	= $db;
		$this->sqldefault['db_host'] = $db_host;
		$this->sqldefault['db_user'] = $db_user;
		$this->sqldefault['db_pass'] = $db_pass;
		$this->sqldefault['db'] = $db;
	}

	function getDBInfo() {
		return "
			hostname: ".$this->db_host."
			database: ".$this->db."
			user: ".$this->db_user;
	}

	function connect_db($host="") {
		$host = (empty($host)) ? $this->db_host : $host;
		$link = @mysqli_connect($host, $this->db_user, $this->db_pass);
		if (!$link || empty($link)) {
			$this->mysqlerror = "= Connect Error: mysql.inc::connect_db - " . mysqli_connect_errno();
			error_log($this->mysqlerror);
			error_log(" host: " . $this->db_host);
			error_log(" user: " . $this->db_user);
			error_log(" pass: " . $this->db_pass);
			error_log("... =");
			return false;
		}
		if(!empty($this->db)) {
			$link = $this->select_db($this->db, $link);
        }
      $this->db_link = $link;
		return $link;
	}

	function select_db($database , $link) {
		$db = mysqli_select_db($link, $database);
		if(!$db) {
			$this->mysqlerror = "Error: ".mysqli_error($link);
			$this->mysqlerrornb = mysqli_errno($link);
			return false;
		}
		// Need to set db attribute to allow it to reconnect
		// Especially when default database was not set when this instance
		// of the class is initiated.
		$this->db = $database;
		return $link;
	}

	function checkDBConnection($host="") {
		$resource = $this->connect_db($host);
		if (is_object($resource)) {
			$this->close_db($resource);
			return True;
		} else {
			return False;
		}
	}

	function close_db($resource_link="") {
		if (empty($resource_link))
			die("Attempting to close non-existent mysql connection.");
		else
			mysqli_close($resource_link);
	}

	function SQLTableExists($name) {
		$table_exists=false;
		$q = "SELECT * from $name limit 1;";
		$Rtables = $this->SQLQuery($q);
		if ($Rtables === false)
			return false;
		return true;
	}
	
	function listTables(){
		
		$Rtables = $this->SQLQuery("SHOW TABLES");
	    
		$listOfTables = array();
		while($table = mysqli_fetch_array($Rtables))
			$listOfTables[] = $table[0];
		
		return $listOfTables;
	}
	
	function getSQLTableDefinition($table) {

	    $crlf = $this->crlf;
	    $backquotestr='`';
	
	    $schema_create = "";
	
	    $schema_create .= "CREATE TABLE IF NOT EXISTS $table ($crlf";
	
	    $result = $this->SQLQuery("SHOW FIELDS FROM $table") or die("show fields error");
	    while($row = mysqli_fetch_array($result))
	    {
	        $schema_create .= "   $backquotestr".$row['Field']."$backquotestr ".$row['Type'];
	
	        if(isset($row["Default"]) && (!empty($row["Default"]) || $row["Default"] == "0")) {
		if ($row["Type"=='timestamp']) {
	            $schema_create .= " DEFAULT ".$row['Default'];
		} else {
	            $schema_create .= " DEFAULT '".$row['Default']."'";
		}
	}
	        if($row["Null"] != "YES")
	            $schema_create .= " NOT NULL";
	        if($row["Extra"] != "")
	            $schema_create .= " ".$row['Extra'];
	        $schema_create .= ",$crlf";
	    }
	    $schema_create = preg_replace("%,%".$crlf."$", "", $schema_create);
	    $result = $this->SQLQuery("SHOW KEYS FROM $table") or die(mysqli_error($this->db_link));
	    while($row = mysqli_fetch_array($result))
	    {
	        $kname=$row['Key_name'];
	        if(($kname != "PRIMARY") && ($row['Non_unique'] == 0))
	            $kname="UNIQUE|$kname";
	         if(!isset($index[$kname]))
	             $index[$kname] = array();
	         $index[$kname][] = $row['Column_name'];
	    }
	
	    foreach ($index as $x =>$columns)
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
	    $result = $this->SQLQuery($local_query) or die(mysqli_error($this->db_link));
	    $i = 0;
			// failed sql query
			if (!is_array($result)) return (true);
	    while($row = mysqli_fetch_row($result))
	    {
	        set_time_limit(60); // HaRa
	        $table_list = "(";
	
           for($j=0; $j<mysqli_num_fields($result);$j++)
           {
             $fieldInfo = mysqli_fetch_field_direct($result,$j);
             $table_list .= "`".$fieldInfo->name."`, ";
           }

	        $table_list = substr($table_list,0,-2);
	        $table_list .= ")";
	
	        if(isset($this->SQL["showcolumns"]))
	            $schema_insert = "INSERT INTO $table $table_list VALUES (";
	        else
	            $schema_insert = "INSERT INTO $table VALUES (";
	
	        for($j=0; $j<mysqli_num_fields($result);$j++)
	        {
	            if(!isset($row[$j]))
	                $schema_insert .= " NULL,";
	            elseif($row[$j] != "")
	                $schema_insert .= " '".addslashes($row[$j])."',";
	            else
	                $schema_insert .= " '',";
	        }
	        $schema_insert = preg_replace("%,$%", "", $schema_insert);
	        $schema_insert .= ")";
	        $content .= trim($schema_insert).";$crlf";
	        $i++;
	    }
	    return (true);
	}

	function setSQLHost($sqlhost) {

		if (!is_array($sqlhost))
			$sqlhost = array();
		$this->db_host	= (array_key_exists('db_host', $sqlhost)) 
					? $sqlhost['db_host'] : $this->sqldefault['db_host'];
		$this->db_user	= (array_key_exists('db_user', $sqlhost)) 
					? $sqlhost['db_user'] : $this->sqldefault['db_user'];
		$this->db_pass	= (array_key_exists('db_pass', $sqlhost)) 
					? $sqlhost['db_pass'] : $this->sqldefault['db_pass'];
		$this->db	= (array_key_exists('db', $sqlhost)) 
					? $sqlhost['db'] : $this->sqldefault['db'];
		return true;
	}

	function getServerInfo() {
		if (!$this->db_link->server_info) {
			$link = $this->connect_db($this->db_host);
			return mysqli_get_server_info($link);
		} else {
			return $this->db_link->server_info;
		}
	}

	function getSQLHost() {
		return $this->db_host;
	}

	function getError() {
		return $this->mysqlerror;
	}

	function getErrorNumber() {
		return $this->mysqlerrornb;
	}

	function getDBName() {
		if (!$r = $this->getSQLResult("SELECT database();")) {
            return 'error';
        } else {
            return ($r[0]["database()"]);
        }
	}

	function getSQLQuery() {
		return $this->sqlquery;
	}

	function getSQLNumRows($query) {
		if (!$result = $this->SQLQuery($query))
			return False;
		if (!is_object($result))
			return $result;
		$numrows = mysqli_num_rows($result);
		return $numrows;
	}

	function _backtrace() {
		ob_start();
		debug_print_backtrace();
		$trace = ob_get_contents();
		ob_end_clean();
		return $trace;
	}

	function SQLQuery($query, $insert=false) {
		// this method is not meant to be called without a provided db at object
		// construction time - see connect_db(). there is still functionality
		// calling it this way, which likely hasn't worked in a long time, and
		// it just fails *after* a connection is established.  fail early instead.
		if(empty($this->db)) {
			return false;
		}

		$this->sqlquery = $query;

		// a private - to this function - $link to avoid it getting
		// trampled - see connect_db() - by the lack of interface and allow
		// for reuse.
		if (empty($this->__SQLQuery_link)) {
			$this->__SQLQuery_link = $this->connect_db($this->db_host);
		}

		// connection failed
		$link = $this->__SQLQuery_link;
		if (!$link) {
			return False;
		}
		mysqli_query($link, "SET sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''))");

        try {
		$result = mysqli_query($link, $query); 
        } catch (Exception $e) {
			$this->mysqlerror = "= Error: mysql.inc::SQLQuery - " . mysqli_error($link);
			$this->mysqlerrornb = mysqli_errno($link);
			// error_log($this->mysqlerror);
			// error_log("  query: " . $query);
			// error_log("  trace: " . $this->_backtrace());
			// error_log("... =");
			return False;
        }

		if ($insert) {
			return mysqli_insert_id($link);
		}

		return $result;
	}

	function getSQLResult($query, $fetch=MYSQLI_ASSOC) {
		$result = $this->SQLQuery($query);
		if (!is_object($result)) {
			if ($result === false) return array();
			return $result;
		}
		$data = array();
		while ($row = mysqli_fetch_array($result, $fetch))
			$data[] = $row;
		return $data;
	}

	function getSQLResultNumList($query) {
		// Get single select query result in the form of tuple-like
		// list to be used in other query.
		// This is used to get around the problem that
		// some operation is not allowed in subquery in MYSQL
		$result = $this->SQLQuery($query);
		if (!is_object($result)) {
			return $result;
		}

		$callback = function($value) {
			return $value[0];
		};

		$r = @mysqli_fetch_all($result, MYSQLI_NUM);
		$r = array_map($callback,$r);
		$joined = implode("','",$r);
		return "('".$joined."') ";
	}

	function SQLQueries($queries) {
		$link = $this->connect_db($this->db_host);
		$q = (is_array($queries)) ? $queries : array($queries);
		foreach($q as $v) {
			mysqli_query($link, $v) or die("Error: $v".mysqli_error($link));
		}
		$this->close_db($link);
		return(true);
	}

	function SQLInsert($table, $data, $db='') {
		if (!$data || !$table || !is_array($data))
			return False;
		$fields = array_keys($data);
		foreach($fields as $k=>$v)
			$fields[$k] = "`".$v."`";
		foreach($data as $k=>$v)
			if (!is_numeric($v))
				$data[$k] = "'".addslashes($v)."'";
		$dbselection = ($db) ? $db.'.':'';
		$q = "INSERT INTO $dbselection`$table` (".implode(', ',$fields).") VALUES (".implode(', ',$data).")";
		return $this->SQLQuery($q,true);
	}

	function array_to_sql($data) {
		if (!is_array($data) || empty($data))
			return False;
		$sqlformat=array();
		foreach ($data as $k=>$v) {
			if (is_null($v)) {
				$sqlformat[] = "`$k` IS NULL";
				continue;
			} elseif (!is_numeric($v)) {
				$v = "'".addslashes($v)."'";
			}
			$sqlformat[] = "`$k`=".$v;
		} 
			$sql .= join(' AND ', $sqlformat);
		return $sql;
	}
	
	function array_to_select($data, $prefix="") {
		if (!$data || !is_array($data))
			return False;
		$sqlformat=array();
		if ($prefix) {
			$prefix.=".";
		}
		foreach ($data as $key=>$field) {
			if (!is_numeric($key))
				$sqlformat[] = "$field";
			else
				$sqlformat[] = $prefix."`$field`";
		}
		$sql .= join(', ', $sqlformat);
		return $sql;
	}

	function SQLInsertIfNotExists($table, $data, $return_id=false) {
		if (!$sql=$this->array_to_sql($data))
			return false;
		$field="1";
		if ($return_id) {
			if ($pKey = $this->getPriKey($table)) {
				$field=$pKey;
			}
		}
		$q = "SELECT $field from `$table` "
			."WHERE $sql";
		$res = $this->SQLQuery($q);
		if ($res && mysqli_num_rows($res)>0) {
			if ($return_id) {
				if ($pKey) {
					$result=mysqli_fetch_array($res);
					return $result[$pKey];
				}
			}
			return true;
		} else {
			$id = $this->SQLInsert($table, $data);
			if (is_bool($id) && !$id)
				return false;
			if ($return_id && $id)
				return $id;
			return true;
		}
		
	}

	function SQLUpdate($table, $data, $where="",$db="") {
		if (!$data || !$table || !is_array($data))
			return False;
		if (is_array($where)) {
			$wherestr = " WHERE ";
			foreach ($where as $k=>$v) 
				$whereformat[] = "`$k`='".addslashes($v)."'";
			$wherestr .= implode(' AND ', $whereformat);
		} else if (!empty($where)) {
			$wherestr .= $where;
		}
		foreach ($data as $k=>$v) {
			if (!is_numeric($v) && $v !== NULL)
				$v = "'".addslashes($v)."'";
			if ($v === NULL) 
				$kv[] = '`'.$k.'`= NULL';
			else
				$kv[] = "`".$k."`=".$v;
		}
		$dbselection = ($db) ? $db.'.':'';
		$q = "UPDATE $dbselection`$table` SET ".implode(', ',$kv).$wherestr;
		if (!$this->SQLQuery($q))
			return False;
		return true;
	}

	function SQLDelete($table, $where="") {
		if (!$table)
			return False;
		if (is_array($where)) {
			$wherestr = " WHERE ";
			foreach ($where as $k=>$v)
				$whereformat[] = "`$k`='".addslashes($v)."'";
			$wherestr .= implode(' AND ', $whereformat);
		} else if (!empty($where)) {
			$wherestr .= $where;
		}
		$q = "DELETE FROM `$table` ".$wherestr;
		if (!$this->SQLQuery($q))
			return False;
		return true;
	}

	function SQLAlterTables($sqldef, $fieldtypes, $engine='') {
		if (!is_array($fieldtypes) || !is_array($sqldef))
			return False;
		$changes = "";
		foreach ($fieldtypes as $table=>$fieldtype) {
			if ($this->SQLTableExists($table)) {
				$orgfieldtype = $this->getFieldTypes($table);
				foreach ($fieldtype as $f=>$t) {
					if (preg_match('%^DEF_%', $f))
						continue;
					if (!$orgfieldtype[$f]) {
						$q[] = "ALTER TABLE `$table` ADD `$f` $t";
						$changes .= "ADD $table $f  => $t <br>";
					} else if ($orgfieldtype[$f]!=$t) {
						$q[] = "ALTER TABLE `$table` CHANGE `$f` `$f` $t";
						$changes .= "CHANGE $table $f  => $t <br>";
					}
				}
			} else {
				$def_q = $sqldef[$table];
				if (!empty($engine)) $def_q = substr_replace($def_q,' ENGINE='.$engine.'; ',-1);
				$q[] = $def_q;
				$changes .= "CREATE $table <br>";
			}
		}
		if (!empty($q))
			$this->SQLQueries($q);
		if ($changes)
			return $changes;
		return False;
	}

	function getPriKey($table) {
		$prikey=false;
		if ($table && $this->SQLTableExists($table)) {
			$R = $this->SQLQuery("SHOW FIELDS FROM `$table`");
			while ($r = mysqli_fetch_array($R))
				if ($r['Key']=='PRI') {
					$prikey = $r['Field'];
					break;
				}
		}
		return $prikey;
	}
	
	function getFields($table) {
		$fields = array();
		if ($table && $this->SQLTableExists($table)) {
			$R = $this->SQLQuery("SHOW FIELDS FROM `$table`");
			while ($r = mysqli_fetch_array($R))
				$fields[] = $r['Field'];
		}
		return $fields;
	}

	function FieldExists($table,$fieldname) {
		$has_field = false;
		$fields = $this->getFields($table);
		if (empty($fields)) return $has_field;
		if (in_array($fieldname,$fields)) $has_field=true;
		return $has_field;
	}

	function getTableDescription($table) {
		$fields = array();
		if ($table && $this->SQLTableExists($table)) {
			return $this->getSQLResult("DESCRIBE `$table`");
		}
		return $fields;
	}

	function getFieldTypes($table) {
		$fields = array();
		if ($table) {
			$R = $this->SQLQuery("SHOW FIELDS FROM `$table`");
			while ($r = mysqli_fetch_array($R))
				$fields[$r['Field']] = $r['Type'];
		}
		return $fields;
	}

	function getTables() {
		$tables = array();
		$R = $this->SQLQuery("SHOW TABLES ");
		if ($R == false) return $tables;
		while ($row = mysqli_fetch_row($R))
			$tables[] = $row[0];

		return $tables;
	}

	function isTable($table) {
		$istable = false;
		$tables = $this->getTables();
		if (in_array($table, $tables))
			$istable = true;
		return $istable;
	}

	function getId($parameters) {
		// --- return id from specified table. $where_fields is an array
		// containing the "where" condition:
		//	field1=>value1, field12=>value2, ...
		if (!$table = $parameters['table'])
			return false;
		if (!$where_fields = $parameters['where'])
			$where_fields=array();
		if (!$id=$parameters['id'])
			$id=$this->getPriKey($table);

		$acq_fields = $this->getFields($table); 
		$where = array();
		foreach ($where_fields as $k=>$f) {
			if (!in_array($k, $acq_fields))
				return false;
			$where[] = "`$k`='".addslashes($f)."'";
		}
		if (empty($where))
			return false;
		$wherestr = implode(' and ', $where);
		$q = 'select `'.$id.'` as id from `'.$table.'`'
			.' where '.$wherestr;
		$R = $this->SQLQuery($q);
		$ids = array();
		while ($r = mysqli_fetch_array($R))
			$ids[] = $r['id'];

		if (count($ids)==1)
			return $ids[0];
		else
			return $ids;
	}

	function getData($parameters, $numrows=false) {
		if (!$table = $parameters['table'])
			return false;
		if (!$select = $this->array_to_select($parameters['field']))
			return false;
		if (is_array($parameters['where'])) {
			$sql_where = $this->array_to_sql($parameters['where']);
			if ($sql_where)
				$sql_where = "WHERE $sql_where";
		}
		if (!$sql_order=$parameters['order'])
			$sql_order="";
		if (!$sql_limit=$parameters['limit'])
			$sql_limit="";
		$q = "SELECT $select from `$table` "
			.$sql_where
			.$sql_order
			.$sql_limit;
		if ($numrows)
			return $this->getSQLNumRows($q);

		return $this->getSQLResult($q);
	}

	function format_date($str, $in="mdy", $out="ymd", $sep="/" ) {
		// --- Month/Day/Year => Year/Month/Day
		$in=array_flip(str_split($in));
		$out=str_split($out);
		$date=explode($sep, $str);
		$ndate=array();
		foreach ($out as $k) { 
			$ndate[]=$date[$in[$k]];
		}
		return implode("/", $ndate);
	}

	function dbError() {
		return "databse error";
	}
}



?>
