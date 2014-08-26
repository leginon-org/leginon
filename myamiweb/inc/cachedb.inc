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
 *  ENABLE_CACHE, CACHE_PATH set in config.php
 *
 */
require_once 'config.php';
require_once 'inc/mysql.inc';

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
