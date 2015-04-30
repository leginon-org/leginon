<?php
/**
 * 
 * @author amber
 * 
 * This is a static class with functions related to path manipulation.
 * 
 * example of how to use it:
 * require_once "path.inc"
 * 
 * $path = Path::formatEndPath($path)
 * 
 */
define('DS', "/");
class Path 
{
	// make sure a path ends with a single path separator.
	public static function formatEndPath( $path, $dirSeparator=DS ) 
	{
		$formattedPath = preg_match("%".$dirSeparator."$%", $path) ? $path : $path.$dirSeparator;
		return $formattedPath;
	}
	
	public static function formatPath($path) 
	{
		$npath = preg_replace('%\\\\%','/',$path);
		$npath = preg_match("%/$%", $npath) ? $npath : $npath."/";
		return $npath;
	}
	
	//--- return path from a string
	public static function getPathFromString($str) 
	{
		$parts = explode('/',$str);
		if (!is_array($parts))
			return $str;
		array_pop($parts);
		return implode('/',$parts);
	}	
	
	// join paths. pass in any number of path snippets.
	// ex. Path::join("/this/is", "my", "/path/to/", "/here")
	// returns "/this/is/my/path/to/here"
	public static function join() 
	{
		$args = func_get_args();
		$paths = array();
		
		foreach($args as $arg) {
		  $paths = array_merge($paths, (array)$arg);
		}
		
		foreach($paths as &$path) {
		  $path = trim($path, '/');
		}
		
		// ensure a leading slash on the first param is left on for absolute paths
		if (substr($args[0], 0, 1) == '/') {
		  $paths[0] = '/' . $paths[0];
		}
		
		return join('/', $paths);
	}
}

?>
