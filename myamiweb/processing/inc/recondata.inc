<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "config_processing.php";
require_once "inc/mysql.inc";

define('RECON_DB_HOST', $RECON_DB_HOST);
define('RECON_DB_USER', $RECON_DB_USER);
define('RECON_DB_PASS', $RECON_DB_PASS);
define('RECON_DB', $RECON_DB);

class recondata {

	var $crlf = "\n";

	function recondata() {
		$this->mysql = new mysql(
					RECON_DB_HOST,
					RECON_DB_USER,
					RECON_DB_PASS,
					RECON_DB);
	}
	
	function getReconIds ($stackId) {
		$q = "select `DEF_id` "
			."from `reconRun` where `dbparticledata|stackParams|stackId` = '$stackId'";
		$r = $this->mysql->getSQLResult($q);
		return $r;
	}

}
?>
