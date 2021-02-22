<?php
	/* This script uses JQueryUI sortable to allow the user to sort and then submit
	target order from an image. JQuery and JQueryUI are under MIT license.
	*/
	require_once 'inc/leginon.inc';

	$sessionId = $_GET['expid'];
	$imgId = $_GET['id'];
	$order_list = $_GET['order'];
	$is_abort = $_GET['abort'];

	function subtractOne($n) {
		return $n-1;
	}
	function addOne($n) {
		return $n+1;
	}
	$rtlist = $leginondata->getTargetListFromImage($imgId);
	if ($rtlist) {
		if ($rtlist['mosaic'] == 1) {
			// given a gr image id and get targets on all tile images on the atlas
			$title = "Targets on atlas ".$rtlist['label'];
			$targets = $leginondata->getNewTargetsFromAtlasImageList($rtlist['ilist']);
		} else {
			// given a non atlas image id and get targets on that image
			$title = "Targets on image ";
			$targets = $leginondata->getNewTargetsOnImage($imgId); 
		}
		if (!is_null($order_list)) {
			// save new order 
			$order_str = "(".$order_list.")";
			$order_array = explode(',', $order_list);
			$order_array = array_map('subtractOne', $order_array);
			if ($targets) {
				$leginondata->saveTargetOrder($sessionId, $targets[0]['tlist'], $order_str);
			//TODO close the dialogue.
			}
		} elseif ($is_abort == 1) {
			if ($targets) {
				$leginondata->saveTargetOrder($sessionId, $targets[0]['tlist'], '()');
				exit();
			}
		} else {
		// retrieve current target order
			$order_result = $leginondata->getTargetOrder($sessionId, $targets[0]['tlist']);
			if (is_array($order_result) && array_key_exists('SEQ|order',$order_result)) {
				$order_array = explode(',',substr($order_result['SEQ|order'],1,-1));
				$order_array = array_map('subtractOne', $order_array);
			} else {
				// make default
				$order_array = range(0,count($targets)-1);
			}
		}
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
			#sortable { list-style-type: none; margin: 0; padding: 0; width: 60%; }
			#sortable li { margin: 0 3px 3px 3px; padding: 0.4em; padding-left: 1.5em; font-size: 1.0em; height: 18px; }
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
	if (is_array($targets) && count($targets)) {
		$str = '<ul id="sortable">';
		for ($i = 0; $i < count($targets); $i++) {
			$t_index = $order_array[$i];
			//$str .= "<li class=\"ui-state-default\" id='".$targets[$t_index]['number']."'><span class=\"ui-icon ui-icon-arrowthick-".$t_index."-n-s\"></span>Target Number ".$targets[$t_index]['number']." on ".$targets[$t_index]['filename'].".mrc</li>".$crlf;
			$str .= "<li class=\"tablebg\" id='".$targets[$t_index]['number']."'><img name=\"thumbtarget_btimg\" src=\"http://localhost/myamiweb/img/target_bt_on.gif\" alt=\"target_bt\" border=\"0\" height=\"15\" vspace=\"0\">Target Number ".$targets[$t_index]['number']." on ".$targets[$t_index]['filename'].".mrc</li>".$crlf;


		}
		$str .= '</ul>'.$crlf;
		$str .= '<table><tbody><tr><td>';
		$str .= "<input class='gobutton' type='button' value='Save new order' onclick=\"submit()\">"; 
		$str .= '</td><td>'.$crlf;
		$str .= "<input class='stopbutton' type='button' value='Abort all targets' onclick=\"submit_abort()\">"; 
		$str .= '</td></tr></tbody></table>'.$crlf;
	} else {
		$str = "No targets found";
	}
	echo $str;
?>
	</body>
</html>
