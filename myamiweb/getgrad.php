<?php

$gradients=array(
	'default'=>'',
	'inverse'=>'inverse linear',
	'heatedobj'=>'heated object',
	'spectrum'=>'spectrum',
);
foreach ($gradients as $gradient=>$val) {
	$imgsrc="img/dfe/grad.php?h=10&amp;w=100&amp;map=".$gradient;
	$img='<img alt="'.$gradient.'" src="'.$imgsrc.'">';
	$html[]="$img : $gradient";
	$styles[]=getcss($gradient);
	$cgradient=preg_replace('%[. #]%','',$gradient);
	$gradientd = ($val) ? $val: "linear";
	$sel = ($gradient==$_GET['gr']) ? 'selected' : '';
	$options[]='<option class="c'.$cgradient.'" value="'.$gradient.'" '.$sel.' >'.$gradientd.'</option>'."\n";

	
}

function getcss($gradient) {
	
	$imgsrc="img/dfe/grad.php?h=10&w=64&map=".$gradient;
	$gradient=preg_replace('%[. #]%','',$gradient);
	$str=".c$gradient {
	background-repeat: no-repeat;
	background-image: url($imgsrc);
	background-position: right center;
}";
	return $str;
}
?>
	<style type="text/css">
	<?php
		echo join("\n", $styles);
	?>
	</style>
	<script type="text/javascript">
		function setgrad() {
			if (selgrad=document.adjustform.gradientlist) {
				if (gradimg=document.getElementById('gradimg')) {
					gradimg.src="img/dfe/grad.php?h=10&w=96&map="+selgrad.value
				}
			}
		}
	</script>
<?php
function displaygrad($options, $imgsrc) {
global $state;
echo '<li>
<select name="gradientlist" style="width: 128px" '.$state.' onchange="setgrad(); update()">';
		echo join("\n", $options);
echo '
</select>';
$imgsrc=preg_replace('%map=.*%','',$imgsrc);
if ($_GET['gr']) {
	$imgsrc.="map=".$_GET['gr'];
}
echo " <img alt='selgrad' id='gradimg' src='$imgsrc'>";
echo '</li>';
}
?>
