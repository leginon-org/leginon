<?php
	/* This script uses JQueryUI sortable to allow the user to sort and then submit
	target order from an image. JQuery and JQueryUI are under MIT license.
	*/
	require_once 'inc/leginon.inc';

	// This script does not take preset, so the imgId needs to be exact.
	$imgId = ($_GET['id']) ? (int)$_GET['id']:null;
	$order_list = $_GET['order'];
	$is_abort = $_GET['abort'];

	function subtractOne($n) {
		return $n-1;
	}
	function addOne($n) {
		return $n+1;
	}
	function currentTargetOrder($leginondata, $sessionId, $targets) {
		if (empty($targets)) return array();
		// retrieve current target order tagged in target number
		$order_result = $leginondata->getTargetOrder($sessionId, $targets[0]['tlist']);
		if (is_array($order_result) && array_key_exists('SEQ|order',$order_result)) {
			$order_array = explode(',',substr($order_result['SEQ|order'],1,-1));
			if ($order_array[0]=="") return array(); //aborted
		} else {
			// make default all targets (base 1)
			$order_array = range(1,count($targets)); 
		}
		// keeps only undone target numbers
		$clean_array = array();
		foreach ($order_array as $n) {
			$status = $leginondata->getTargetStatus($targets[0]['tlist'],(int)$n);
			if ($status && strcmp($status,'done')!=0 && strcmp($status,'aborted')!=0) $clean_array[]=$n;
		}
		$order_array = array_map('subtractOne', $clean_array);
		return $order_array; //base 0
	}

	//Need version 0 so that targets are complete.
	//Leginon only generates targets on images of newer versions if targets are not done.
	$imgId = $leginondata->getVersionZeroImage($imgId);
	if (empty($imgId)) exit();
	$rtlist = $leginondata->getTargetListFromImage($imgId);
	if ($rtlist) {
		$sessionId = $rtlist['session'];
		if ($rtlist['mosaic'] == 1) {
			// given a gr image id and get targets on all tile images on the atlas
			$is_mosaic = true;
			$title = "Targets on atlas ".$rtlist['label']."<br><hr>";
			//Targets with new status. This is a complete list of targets necessary to
			//map order_array later
			$targets = $leginondata->getNewTargetsFromAtlasImageList($rtlist['ilist']);
		} else {
			// given a non atlas image id and get targets on that image
			$is_mosaic = false;
			//Targets with new status. This is a complete list of targets necessary to
			//map order_array later
			$targets = $leginondata->getNewTargetsOnImage($imgId); 
			$filename_r = $leginondata->getFilename($imgId);
			$filename = $filename_r[0]['filename'];
			$title = "Targets on image <br> <ul><li>".$filename."</li></ul><hr>";
		}
		if (!is_null($order_list)) {
			// save new order 
			$order_str = "(".$order_list.")";
			// order list from JQueryUI is base 1
			$order_array = explode(', ', $order_list);
			// convert to base 0
			$order_array = array_map('subtractOne', $order_array);
			if ($targets) {
				$leginondata->saveTargetOrder($sessionId, $targets[0]['tlist'], $order_str);
			//TODO close the dialogue.
			}
		} elseif ($is_abort == 1) {
			// aborting
			if ($targets) {
				if ($is_mosaic) {
					//targetlist on mosaic grid atlas is never done.
					//Need to make individual target status done.
					$order_array = currentTargetOrder($leginondata, $sessionId, $targets);
					// the targets not in order_arry should be done already
					for ($i = 0; $i < count($targets); $i++) {
						$t_index = $order_array[$i];
						$t = $targets[$t_index];
						//Only do this on non-done/aborted targets
						$status = $leginondata->getTargetStatus($t['tlist'],$t['number']);
						if ($status && $status != 'done' && $status != 'aborted')
							$leginondata->updateTargetStatus($t['tid'],'aborted');
					}
				} else {
					//insert as DoneImageTargetListData will eliminate pre-processing stuff
					// such as revertStageZ
					$leginondata->saveDoneTargetList($sessionId, $targets[0]['tlist']);
				}
				$leginondata->saveTargetOrder($sessionId, $targets[0]['tlist'], '()');
			}
		}
		$order_array = currentTargetOrder($leginondata, $sessionId, $targets);
	}

	$crlf="\n";
	echo $title;
?>
<html>
	<head>
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, initial-scale=1">
		<title>Target Sorter</title>
		<link rel="stylesheet" type='text/css' href='css/viewer.css'>
		<style>
			#sortable { list-style-type: none; margin: 0; padding: 0; width: 100%; }
			#sortable li { margin: 0 3px 3px 3px; padding: 0.4em; padding-left: 1.5em; font-size: 0.8em; height: 15px; }
			#sortable li span { position: absolute; margin-left: -1.3em; }
		</style>

		<script type="text/javascript" src="js/jquery.js"></script>
		<script type="text/javascript" src="js/jquery-ui/jquery-ui.js"></script>
		<script>
			$( function() {
				$( "#sortable" ).sortable();
				$( "#sortable" ).disableSelection();
			} );
			function submit() {
				var idsInOrder = $( sortable ).sortable("toArray");
				var url = new URL(document.URL);
				url.searchParams.set('order', idsInOrder);
				window.location.href = url.href;
			}
			function submit_abort() {
				var url = new URL(document.URL);
				var answer = confirm("Are you sure you want to abort ?");
				if (answer == true) {
					url.searchParams.set('abort', 1);
				}
				window.location.href = url.href;
			}
		</script>
	</head>
	<body>
 
<?php
	// Show target list
	if (is_array($targets) && count($targets) && $order_array) {
		$str = '<ul id="sortable">';
		for ($i = 0; $i < count($targets); $i++) {
			$t_index = $order_array[$i];
			$postfix = ($is_mosaic) ? 'on '.$targets[$t_index]['filename'].".mrc": '';
			if (is_numeric($t_index)) {
				$str .= "<li class=\"fittable\" id='".$targets[$t_index]['number']."'>";
				$str .= "<img name=\"thumbtarget_btimg\" src=\"img/target_bt_on.gif\" alt=\"target_bt\" border=\"0\" height=\"15\" vspace=\"0\">";
				$str .= "Target <b>".$targets[$t_index]['number']."</b> ".$postfix."</li>".$crlf;
			}

		}
		$str .= '</ul>'.$crlf;
		$str .= '<table style="width:100%"><tbody><tr><td style="width:50%">';
		$str .= "<input class='gobutton' type='button' value='Save new order' onclick=\"submit()\">"; 
		$str .= '</td><td style="text-align:right">'.$crlf;
		$str .= "<input class='stopbutton' type='button' value='Abort all targets' onclick=\"submit_abort()\">"; 
		$str .= '</td></tr></tbody></table>'.$crlf;
	} else {
		$str = '<br><br>No active target found';
	}
	echo $str;
?>
	</body>
</html>
