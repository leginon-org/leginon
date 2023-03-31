<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
//require_once "inc/graph.inc";

?>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css">
<title> Ptolemy active learning progress on the grid atlas tile image </title>
</head>
<body>
<?php

$defaultId= 430;
$default_tile_imageId=7510;
$sessionId= ($_GET[session]) ? $_GET[session] : $defaultId;
$tile_imageId = ($_GET[id]) ? $_GET[id] : $default_tile_imageId;

$info=$leginondata->getImageInfo($tile_imageId);
if ($info['parentpreset']) {
	echo "<h2> ".$info['filename']." is not an atlas tile </h2>";
	echo "<hr>";
	exit;
}
$targets = $leginondata->getImageTargets($tile_imageId, $type="acquisition");
if (!$targets) {
	echo "<h2> no target on tile image ".$info['filename']."</h2>";
	echo "<hr>";
	exit;
}
echo "<h2> targe order and score over time on tile image ".$info['filename']."</h2>";
echo "<h4> * legend: target number - score</h4>";
echo "<h4> * Red border marks target processed </h4>";
echo "<hr>";
$tlist = $targets[0]['tlist'];	
$all_scores = $leginondata->getSquareTargetScores($sessionId, $tile_imageId);
$all_data = $leginondata->getTargetNumberByOrderOnTileImage($sessionId, $tile_imageId);
$no_score = (count($all_scores) == 0); # older data is hard to get score. igore for now.
// offset is needed if there are targets first manually selected since no scores were saved then..
$offset= count($all_data)-count($all_scores);
$offset= ($offset > 0 && !$no_score) ? $offset:0;
if (true) {
	echo "<table><tr><th>time</th>";
	echo "<tr>";
	for ($j=0; $j<count($all_data); $j++) {
		$d = $all_data[$j];
		$scores = $all_scores[$j-$offset];
		echo "<td>";
		if ($j==0) $d0=$d['unix_timestamp'];
		$tdiff = $d['unix_timestamp']-$d0;
		echo sprintf('%.1f min',$tdiff/60);
		echo "</td>";
		// $d has key unix_timestamp and the targets
		for ($i=0; $i<count($d); $i++) {
			$n = $d[$i]; # target_number
			// score data from target at target_number n
			$t_data = $scores[$n];
			if ($t_data == null && !$no_score) continue;
			//
			if (!$no_score) {
				// show scores
				$set_number = $scores['set_number'];
				$targetId = $t_data['tId'];
				//Skip if the best score for this target is a ptolemy square on another
				//parent tile image.
				$squares = $leginondata->getTargetPtolemySquares($sessionId, $targetId);
				if (is_array($squares) && count($squares)> 1) {
					$best_score = -1.0;
					$best_tile_id = 0;
					foreach ($squares as $sq) {
						$my_sqId = $sq['ptolemy_square_id'];
						$my_score = $leginondata-> getPtolemyScoreHistoryData($sessionId, null, $my_sqId, $n, $set_number)[0];
						if ($my_score['score'] > $best_score) {
							$best_score = $my_score['score'];
							$best_tile_id = $my_score['tile_id'];
						}
					}
					if ($best_tile_id != $tile_imageId) continue;
				} else {
					// one ptolemy square per target;
					$best_score = $t_data['score'];
				}
				$best_score = sprintf('-%.5f', $best_score)+0.0;
			} else {
				$best_score = '';
			}
			// add border if done
			$status = $leginondata->getTargetStatus($tlist, $n);
			$border_color= ($status=='done') ? 'red': 'white';
			echo "<td>";
			echo '<table><tr><td style="border:3px;border-style:solid;border-color:'.$border_color.';">';
			echo '<img src="jpg_crop.php?imageId='.$tile_imageId.'&size=120&tnumber='.$n.'" width=64 heigh=64>';
			echo "</td></tr>";
			echo "<tr><td>".$n.$best_score."</td>";
			echo "</td></tr></table>";
			echo "</td>";
		}
		echo "</tr>";
	}
	echo "</table>";
	exit;
}
?>
</body>
</html>
<?php
?>
