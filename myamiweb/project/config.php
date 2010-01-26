<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 * $Source: /export/sw/cvsroot/projectdb/config.php,v $
 * $Revision: 1.3 $
 * $Name:  $
 * $Date: 2007/02/21 17:56:00 $
 * $Author: dfellman $
 * $State: Exp $
 * $Locker:  $
 *
 */

require "../config.php";

// --- Leginon database config
$VIEWER_URL = BASE_URL."/3wviewer.php?expId=";
$SUMMARY_URL = BASE_URL."/summary.php?expId=";
$UPLOAD_URL = BASE_URL."/processing/uploadimage.php";

$DEF_PROJECT_TABLES_FILE = "defaultprojecttables.xml";

// --- default for processing db --- //
$DEF_PROCESSING_TABLES_FILE = "defaultprocessingtables.xml";

// --- do not remove --- //
set_include_path(get_include_path() . PATH_SEPARATOR . $BASE_PATH);
?>
