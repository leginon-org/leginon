<?
class project {

	function project(){
		require("config.php");
		$this->mysql = new mysql(	$PROJECT_HOSTNAME, $PROJECT_DBUSER,
						$PROJECT_DBPASSWORD, $PROJECT_DATABASE);
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

}
?>

