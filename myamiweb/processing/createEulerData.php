<?php
require "inc/particledata.inc";
require "inc/euler.inc";

	if (!$reconId=$_REQUEST['reconId']) {
		if ($reconId || !$reconId=$argv[1])	{
			echo "no reconId \n";
			exit;
		}
	}

	$particle = new particledata();
	$info = $particle->getIterationInfo($reconId);
	$total_iter=count($info);
	for($i = 1; $i<$total_iter; $i++)
		save(getData($reconId,$i,$i+1));

	function getData($reconId, $iter1,$iter2)
	{
		//query	
		global $particle;
		$ref = $particle->getRefinementData($reconId,$iter1);
		$refine1 = $ref[0];
		$ref = $particle->getRefinementData($reconId,$iter2);
		$refine2 = $ref[0];
		$commonprtls = $particle->getCommonParticles($refine1['DEF_id'], $refine2['DEF_id']);
		$eulers1 = array();
		$eulers2 = array();
		foreach ($commonprtls as $k) {
			$eulers1[]=eulerArray(deg2rad($k['euler1_1']), deg2rad($k['euler1_2']), deg2rad($k['rot1']));
			$eulers2[]=eulerArray(deg2rad($k['euler2_1']), deg2rad($k['euler2_2']), deg2rad($k['rot2']));
		}
		//math
		//everything is stored in a statistics object
		//(mean, std, min, max, and data)
		$stats = getStats($reconId, $iter1,$iter2,$eulers1,$eulers2);
		return $stats;
	}
	function eulerArray($a, $b, $c) {
		return array('a'=>$a, 'b'=>$b, 'c'=>$c);
	}
	//funtion that writes all the datat in $stats to the database
	function save($stats)
	{
		global $particle;
		$particle->insertEulerStats($stats);
	}
?>
