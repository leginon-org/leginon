<?php
/**
 *	@version $Revision: 1.4 $
 *	@version $Id: cachedb.inc,v 1.4 2006-04-07 20:40:06 suloway Exp $
 */
/**
 *	cachedb: a class to cache any data in a db.	
 *	
 */

require_once 'inc/mysql.inc';

function startcache($session) {
	if (ENABLE_CACHE!=1) {
		return;
	}
  $script=CACHE_SCRIPT;
  if (isrunning($script, "session=$session")) {
    return;
  }
  $outpath=CACHE_PATH.$session;
  $log=CACHE_PATH.$session.".log";
  $option="session='$session' s=512 outpath='$outpath'";
  $cmd="/usr/bin/php -q $script $option > $log &";
  exec($cmd);
}

function isrunning($cmd, $pattern) {
  $isrunning=false;
  $cmd="ps -ef | grep $cmd";
  exec($cmd, $res);
  foreach($res as $row) {
    if (ereg($pattern, $row)) {
      $isrunning=true;
      break;
    }
  }
  return $isrunning;
}

class cachedb {

	function cachedb($hostname, $db_user, $db_pass, $database) {
		$this->mysql = new mysql($hostname, $db_user, $db_pass, $database);
	}

	function get($uri) {
		$checksum = $this->mkchecksum($uri);
		if (!$id = $this->exists($checksum))
			return False;

		$q = "select `image` "
			."from `images` "
			."where `id`='".$id."'";
		$Rq = $this->mysql->SQLQuery($q);
		$r = mysql_fetch_array($Rq, MYSQL_ASSOC);
		return $r['image'];
	}

	function put($uri, $blob=False, $force=False) {
		$checksum = $this->mkchecksum($uri);
		if (!$force)
			if ($id = $this->exists($checksum))
				return $checksum;

		if ($blob)
			$imgblob=$this->mkbinblob($blob);
		else
			if (!$imgblob=$this->mkbinblobfromfile($uri))
				return False;

		$q =	"insert into images "
			."(`checksum`, `image`) "
			."values "
			."('".$checksum."',".$imgblob.")";

		if (!$id = $this->mysql->SQLQuery($q, True))
			return False;

		return $checksum;
	}

	function exists($checksum) {
		$q = "select `id` "
			."from `images` "
			."where `checksum`='".$checksum."'";
		$Rq = $this->mysql->SQLQuery($q);
		$r = mysql_fetch_array($Rq);
		if (!$id = $r['id'])
			return False;
		return $id;
	}

	function flushAll() {
		if($this->mysql->SQLQuery('delete from `image`'))
			return True;
		return False;
	}

	function mkchecksum($string) {
		return 	md5($string);
	}

	function mkbinblobfromfile($uri) {
	//	list($protocol, $uri) = split('//', $url);
	//	$data = file_get_contents($protocol . '//' . urlencode($uri));
		$data = file_get_contents($uri);
		$blob = mkbinblob($data);
	}

	function mkbinblob($data) {
		if (!$data)
			return False;
		$blob = '0x'.bin2hex($data);
		return $blob;
	}
}
?>
