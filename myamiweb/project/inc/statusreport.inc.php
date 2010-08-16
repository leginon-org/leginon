<?

class statusreportdata {

	function statusreportdata($mysql=""){
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB);
	}

	function getFormatedReports($projectId) {
		$strreports="";
		$reports = $this->getStatusReports($projectId, true);
		$crlf = "\n";
		foreach($reports as $r) {
			$strreports.= "________________________________________________".$crlf;
			$strreports.= $r['date'].$crlf;
			$strreports.= $crlf;
			$strreports.= $r['statusreport'].$crlf;
			$strreports.= $crlf;
		}
		return $strreports;
	}

	function getStatusReports($projectId, $complete=false) {
		$statusreports=array();
		$statusreportformat = ($complete) ? 'statusreport' :
			"concat(substring_index(left(statusreport, 110),'\n',2),' ...') as `statusreport`";
		$q='select statusreportId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .$statusreportformat
		   .' from statusreports '
		   .'where projectId="'.$projectId.'" '
		   .'order by timestamp desc';
		$RstatusreportInfo = $this->mysql->SQLQuery($q);
		while ($row = mysql_fetch_array($RstatusreportInfo))
			$statusreports[]=array(
			0 => $row[statusreportId], 'statusreportId' => $row[statusreportId],
			1 => $row[timestamp], 'timestamp' => $row[timestamp],
			2 => $row[date], 'date' => $row[date],
			3 => $row[statusreport], 'statusreport' => $row[statusreport] );
		return $statusreports;
	}

	function getStatusReport($statusreportId, $complete=false) {
		$statusreport=array();
		$statusreportformat = ($complete) ? 'statusreport' :
			"concat(substring_index(left(statusreport, 110),'\n',4),' ...') as `statusreport`";
		$q='select statusreportId, timestamp, '
		   .'date_format(timestamp, "%d-%b-%Y") as `date`, '
		   .$statusreportformat
		   .' from statusreports '
		   .'where statusreportId="'.$statusreportId.'" '
		   .'order by timestamp desc';
		$RstatusreportInfo = $this->mysql->SQLQuery($q);
		$statusreport = mysql_fetch_array($RstatusreportInfo);
		return $statusreport;
	}


	function deleteStatusReport($statusreportId) {
		if (!$statusreportId) return false;
		$q[]='delete from statusreports where statusreportId="'.$statusreportId.'"';
		$this->mysql->SQLQueries($q);
		return true;
	}

	function checkIfStatusReportExists($projectId, $statusreport) {
		if (!$statusreport) return false;
		$q=' select statusreportId from statusreports where '
			.' projectId="'.$projectId.'" and statusreport="'.$statusreport.'"';
		$RstatusreportInfo = $this->mysql->SQLQuery($q);
		$statusreportInfo = mysql_fetch_array($RstatusreportInfo);
		return $statusreportInfo[statusreportId];
	}

	function addStatusReport($projectId, $statusreport="") {
		if (empty($statusreport))
			return false;
		if (!get_magic_quotes_gpc())
		    $statusreport= addslashes($projectId, $statusreport);
		if ($checkstatusreportId=$this->checkIfStatusReportExists($projectId, $statusreport))
			return false;

		$q = "insert into statusreports "
			  ."(projectId, statusreport) "
			  ."values "
			  ."('".$projectId."', "
			  ." '".$statusreport."') ";
		$statusreportId =  $this->mysql->SQLQuery($q, true);
		return $statusreportId;
	}

}
?>
