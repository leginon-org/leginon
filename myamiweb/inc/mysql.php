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
	var $db;
	var $sqldefault = array();
	var $SQL = array ( 
		'showcolumns'=>1,
		'where'=>" WHERE 1 "
		);
	var $crlf = "\n";

	function mysql ($db_host, $db_user, $db_pass, $db) {
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
         $this->mysqlerror = "Connect Error: " . mysqli_connect_errno();
			return False;
		}
		$db = mysqli_select_db($link, $this->db);
		if(!$db) {
			$this->mysqlerror = "Error: ".mysqli_error($link);
			$this->mysqlerrornb = mysqli_errno($link);
			return False;
		}
      $this->db_link = $link;
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
		$Rtables = $this->SQLQuery("SHOW TABLES");
	    	while($table = mysqli_fetch_array($Rtables))
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
	    $result = $this->SQLQuery($local_query) or die(mysqli_error($this->db_link));
	    $i = 0;
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

	function getSQLHost() {
		return $this->db_host;
	}

	function getError() {
		return $this->mysqlerror;
	}

	function getErrorNumber() {
		return $this->mysqlerrornb;
	}

	function getSQLQuery() {
		return $this->sqlquery;
	}

	function SQLQuery($query, $insert=false) {
		$this->sqlquery = $query;
      $link = $this->connect_db($this->db_host);
		if (!$link) {
         $this->mysqlerror = "Connect Error: " . mysqli_connect_errno();
         return False;
		}
		$result = mysqli_query($link, $query); 
		if (!$result) {
			$this->mysqlerror = "Error: ".mysqli_error($link);
			$this->mysqlerrornb = mysqli_errno($link);
			return False;
		}
		if ($insert)
			$res = mysqli_insert_id($link);
		else
			$res = $result;
		$this->close_db();
		return $res;
	}

	function getSQLResult($query, $fetch=MYSQLI_ASSOC) {
		if (!$result = $this->SQLQuery($query))
			return False;
		if (!is_object($result))
			return $result;
		$data = array();
		while ($row = mysqli_fetch_array($result, $fetch))
			$data[] = $row;
		return $data;
	}

	function SQLQueries($queries) {
		$link = $this->connect_db($this->db_host);
		$q = (is_array($queries)) ? $queries : array($queries);
		foreach($q as $v) {
			mysqli_query($link, $v) or die("Error: $v".mysqli_error($link));
		}
		$this->close_db();
		return(true);
	}

	function SQLInsert($table, $data) {
		if (!$data || !$table || !is_array($data))
			return False;
		$fields = array_keys($data);
		foreach($fields as $k=>$v)
			$fields[$k] = "`".$v."`";
		foreach($data as $k=>$v)
			if (!is_numeric($v))
				$data[$k] = "'".addslashes($v)."'";
		$q = "INSERT INTO `$table` (".implode(', ',$fields).") VALUES (".implode(', ',$data).")";
		return $this->SQLQuery($q,true);
	}

	function array_to_sql($data) {
		if (!$data || !is_array($data))
			return False;
		$sqlformat=array();
		foreach ($data as $k=>$v) {
			if (!is_numeric($v))
				$v = "'".addslashes($v)."'";
			$sqlformat[] = "`$k`=".$v;
		} 
			$sql .= join(' AND ', $sqlformat);
		return $sql;
	}

	function array_to_select($data) {
		if (!$data || !is_array($data))
			return False;
		$sqlformat=array();
		foreach ($data as $field) {
			$sqlformat[] = "`$field`";
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

	function SQLUpdate($table, $data, $where="") {
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
			if (!is_numeric($v))
				$v = "'".addslashes($v)."'";
			$kv[] = "`".$k."`=".$v;
		}
		$q = "UPDATE `$table` SET ".implode(', ',$kv).$wherestr;
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

	function SQLAlterTables($sqldef, $fieldtypes) {
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
				$q[] = $sqldef[$table];
				$changes .= "CREATE $table <br>";
			}
		}
		if ($q)
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

	function getData($parameters) {
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
		return $this->getSQLResult($q);
	}

}



?>
