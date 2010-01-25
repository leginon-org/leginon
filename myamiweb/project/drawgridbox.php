<?php
require_once 'inc/project.inc.php' ;
require_once 'inc/gridbox.inc.php' ;
require_once 'inc/mysql.inc';
$grids = array();
$gridboxId = ($_GET['gl']) ? $_GET['gl'] : "";
$gridId = ($_GET['gid']) ? $_GET['gid'] : "";
$size = ($_GET['size']) ? $_GET['size'] : "";
$gridbox = new gridbox();
$gridboxinfo = $gridbox->getGridBoxInfo($gridboxId);
$boxtypeId = $gridboxinfo['boxtypeId'];

switch ($boxtypeId) {
	case '1':
		$gridboxcryo = new gridboxcryo();
		$gridboxcryo->selectedGrid($gridId);
		$gridboxcryo->drawGrids($gridboxId);
		$gridboxcryo->display();
		break;
	case '2':
		$dgridbox = new drawgridbox($size);
		$dgridbox->selectedGrid($gridId);
		$dgridbox->drawGrids($gridboxId);
		$dgridbox->display();
		break;
	case '3':
		$tray = new tray($size);
		$tray->selectedGrid($gridId);
		$tray->drawGrids($gridboxId);
		$tray->display();
		break;
	default:
		blank();
		break;
}
?>

