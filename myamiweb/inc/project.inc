<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

define(DEFAULT_PROJECT, 'all'); 
define(PROJECT_DB_HOST, $PROJECT_DB_HOST);
define(PROJECT_DB_USER, $PROJECT_DB_USER);
define(PROJECT_DB_PASS, $PROJECT_DB_PASS);
define(PROJECT_DB, $PROJECT_DB);

class project {

	function project(){
		$this->mysql = new mysql(	PROJECT_DB_HOST, PROJECT_DB_USER,
						PROJECT_DB_PASS, PROJECT_DB);
        }

	function checkDBConnection() {
		return $this->mysql->checkDBConnection();
	}

	function getGridInfo($gridId){
                $info=array();
                $q='select gridId, label as "label", '
                  .'date_format(prepdate,"%m/%e/%Y") as prepdate, '
                  .'specimenId, '
                  .'substrate, '
                  .'preparation, '
                  .'number, '
                  .'note, '
                  .'boxId, '
                  .'peopleId '
                  .'from grids '
                  .'where gridId="'.$gridId.'"';

                $RgridInfo = $this->mysql->SQLQuery($q);
                $info = mysql_fetch_array($RgridInfo, MYSQL_ASSOC);
                return $info;
	}

	function getProjects($type=""){
                $projects = array();
		if ($type=="all")  
			$projects[] = array(	0 => DEFAULT_PROJECT, 'id' => DEFAULT_PROJECT,
						1 => DEFAULT_PROJECT, 'name' => DEFAULT_PROJECT);
                $q='select projectId, name  from projects';
                $RprojectInfo = $this->mysql->SQLQuery($q);
                while ($row = mysql_fetch_array($RprojectInfo))
                        $projects[]=array(0 => $row[projectId], 'id' => $row[projectId],
                                          1 => $row[name], 'name' => $row[name] );
                return $projects;
        }

}
?>

