<?
if(!extension_loaded('mrc')) {
	dl('mrc.' . PHP_SHLIB_SUFFIX);
}
$module = 'mrc';
$functions = get_extension_funcs($module);
echo "\n";
echo "Functions available in [$module] extension:\n";
echo "\n";
foreach($functions as $func) {
    echo "	".$func."\n";
}
echo "\n";
?>
