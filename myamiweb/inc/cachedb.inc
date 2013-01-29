<?php

/**
 *	The Leginon software is Copyright 2003
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement see
 *	@licence http://ami.scripps.edu/software/leginon-license
 *	@version $Revision: 1.84 $
 *	@version $Id: cache.inc,v 1.84 2008-02-05 18:16:12 dfellman Exp $
 */
/**
 *
 *	cachedb.inc: functions to cache images using makejpg.php
 *  ENABLE_CACHE, CACHE_SCRIPT, CACHE_PATH set in config.php
 *
 */
require_once 'config.php';
require_once 'inc/mysql.inc';

function startcache($session) {
	if (ENABLE_CACHE != 1) {
		return;
	}
	
	$script = CACHE_SCRIPT;
	
	// If the cache script is already running, return
	if (isrunning($script, "session=$session")) {
		return;
	}
	
	updateCacheTime($session);
	
	$outpath = CACHE_PATH.$session;
	if (!is_dir(CACHE_PATH)) {
		exec("mkdir ".CACHE_PATH);
	}
	$log 	= CACHE_PATH.$session.".log";
	$option = "session='$session' s=512 outpath='$outpath'";
	
	if (!is_dir($outpath)) {
		exec("mkdir $outpath");
	}
	
	// This command is being sent to makejpg.php
	$cmd = "/usr/bin/php -q $script $option > $log &";
	exec($cmd);
}

function isrunning($cmd, $pattern) {
	$isrunning=false;
	$cmd="ps -ef | grep $cmd";
	exec($cmd, $res);
	$numOfRun = count($res);

	// not allow more than two caching processing running at the same time.
	// the reason to put 4 is because "ps" use one and "grep" use one.
	if($numOfRun >= 4)
	return true;
	$pattern = "%".$pattern."%";
	foreach($res as $row) {
		if (preg_match($pattern, $row)) {
			$isrunning=true;
			break;
		}
	}
	return $isrunning;
}

function updateCacheTime($session) {
	$dbc = new mysql(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
	$q = "replace `viewer_cache` set session='".$session."'";

	$result = $dbc->SQLQuery($q);
}

function useCache($filepath,$sessionname,$is_fft=false,$cacheonly) {
	//search for imcache jpg file.
	$filename = basename($filepath);
	if (!$is_fft)
		$jpgfilename = preg_replace('%.mrc$%', '.jpg', $filename);
	else
		$jpgfilename = preg_replace('%.mrc$%', '.pow.jpg', $filename);
	$jpgpath = CACHE_PATH.$sessionname."/";
	$jpgpic = $jpgpath.$jpgfilename;
	// not to return the mrc filepath if only allows jpg filepath to return
	if ($cacheonly) $filepath = false;
	if (@is_file($jpgpic)) $filepath = $jpgpic;
	return $filepath;
}

?>
