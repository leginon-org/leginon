<?php
require_once('config.php');
@require_once('getid3/getid3.php');
	function addFlashPlayerJS() {
		if (defined('FLASHPLAYER_URL')) {
			return '<script type="text/javascript" src="/flashplayer/flowplayer.js"></script>'."\n";
		}
	}

	function getMovieSize($filename) {
		if (!class_exists('getID3')) {
			// give a default size to avoid error
			return array(0,0);
		}
		$getID3 = new getID3;
		$i = $getID3->analyze($filename);
		$w = $i['flv']['meta']['onMetaData']['width'];
		$h = $i['flv']['meta']['onMetaData']['height'];
		return array($w, $h);
	}

	function getFinalSizeByLimit($moviename,$limitaxis='width',$max_size=400,$default_width=400,$default_height=400) {
		list($movie_width,$movie_height) = getMovieSize($moviename);
		if ($movie_width > 0 && $movie_height > 0) {
			if ($limitaxis == 'width') {
				$colwidth = ($max_size < $movie_width) ? $max_size : $movie_width;
				$rowheight = $colwidth * $movie_height / $movie_width;
			} else {
				$rowheight = ($max_size < $movie_height) ? $max_size : $movie_height;
				$colwidth = $rowheight * $movie_width / $movie_height;
			}
		} else {
			if ($limitaxis == 'width') {
				$colwidth = ($max_size < $default_width) ? $max_size : max($default_width,40);
				$rowheight = $colwidth * max($default_height,0) / max($default_width,1);
			} else {
				$rowheight = ($max_size < $default_height) ? $max_size : max($default_height,40);
				$colwidth = $rowheight * max($default_width,0) / max($default_height,1);
			}
		}
		return array($colwidth,$rowheight);
	}

	function getMovieHTML($moviefile,$display_width=400,$display_height=400,$subid='') {
		if (!file_exists($moviefile)) return '';
		if (!defined('FLASHPLAYER_URL')) {
			return "<p style='color: #FF0000'>FLASHPLAYER_URL is not defined in config.php</p>";
		}
		if ($display_width <=0 || $display_height <=0) {
			return "<p style='color: #FF0000'>invalid display size</p>";
		}
		$html = '<a  
			 href="'.BASE_URL.'getflv.php?file='.$moviefile.'"
			 style="display:block;width:'.$display_width.'px;height:'.$display_height.'px"  
			 id="player'.$subid.'"> 
		</a>'."\n".' 
		<!-- this will install flowplayer inside previous A- tag. -->
		<script>
			flowplayer("player'.$subid.'", "'.FLASHPLAYER_URL.'FlowPlayerJS.swf",
				{
					clip: {
						autoPlay: true,
						onBeforeFinish: function() {return false;},
					},
					plugins: {
						controls:null
					}
				}
			);
		</script>';
		return $html;
	}
?>
