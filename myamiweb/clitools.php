<?php
/**
 * Tools:
 *	- mkdirs
 *	- getargs
 */

function getargs($args) {
	$data=array();
	foreach($args as $arg) {
		list($k,$v)=explode("=",$arg);
		if ($k && $v) {
			$v=trim($v);
			$va=explode(",",$v);
			if (count($va)>1) {
				$v=array_map("trim", $va);
			}
			$k=ereg_replace("^-|^--", "", $k);
			$data[$k]=$v;
		} else {
			$data['argv'][]=$arg;
		}
	}
	return $data;
}

function mkdirs($path) {
  $p = explode("/",$path);
  foreach($p as $d) {
    $nd[] = $d;
    @mkdir(join("/",$nd));
  }
}

function getdirs($dir=".") {
	$dirs=array();
	if ($handle = opendir($dir)) {
			while (false !== ($file = readdir($handle))) {
					if (is_dir($file) && !ereg("^\.{1,2}$", $file))
						$dirs[]=$file;
			}
			closedir($handle);
	}
	sort($dirs);
	return $dirs;
}

function getfiles($dir=".") {
	$files=array();
	if ($handle = opendir($dir)) {
			while (false !== ($file = readdir($handle))) {
					if (is_file($dir.'/'.$file)) {
						$files[]=$file;
					}
			}
			closedir($handle);
	}
	sort($files);
	return $files;
}

?>
