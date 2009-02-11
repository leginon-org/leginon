<?php
	require "inc/particledata.inc";
	require "inc/leginon.inc";
	require "inc/project.inc";
	require "inc/viewer.inc";
	require "inc/processing.inc";
	require "inc/euler.inc";
	require "inc/jpgraph.php";
	require "inc/jpgraph_scatter.php";

	$begin=getmicrotime();
	$reconId=$_GET['reconId'];
	$iter=$_GET['iter'];

	$reconId=159;
	$reconId=118;
	$reconId=158;
	$iter = 1;

	$particle = new particledata();
	$info = $particle->getIterationInfo($reconId);
	$total_iter=count($info);
	//print_r($info);

	if(!$iter) {
		//echo "Total Iter: $total_iter";
		$data = array();
		for($i = 1; $i<$total_iter; $i++) {
			$stats = getData($reconId, $i,$i+1);
			$data[] = rad2deg($stats->myMean); 
		}
		createGraph($data, "eulerTests/graph_$reconId.png");
	} else {
		for($i = 1; $i<=$total_iter; $i++) {

			echo "getTriangleData...\n";
			$stats = getTriangleData($reconId, $i,$i+1);

			echo "createTriangle...\n";
			$myImage = createTriangle($stats->eulers1);

			$outfile = "eulerTests/image_".$reconId."_$i.png";
			echo "Writing to file... ".$outfile."\n";
			imagepng($myImage, $outfile);

			echo "Done iter $i of $total_iter\n";
		}
	}
	$end=getmicrotime();
	echo "total time: ".($end-$begin)." sec\n";

//********************************************
//********************************************
// END PROGRAM
//********************************************
//********************************************

	function eulerArray($a, $b, $c) {
		return array('a'=>$a, 'b'=>$b, 'c'=>$c);
	}

	function toFloat($s) {
		return floatval($s);
	}

	function getTriangleData($reconId, $iter1,$iter2) {
		//query	
		global $particle;
		$ref = $particle->getRefinementData($reconId,$iter1);
		$refine1 = $ref[0];
		$ref = $particle->getRefinementData($reconId,$iter2);
		$refine2 = $ref[0];
		$commonprtls = $particle->getParticlesFromRefinementId($refine1['DEF_id']);
		//$commonprtls = $particle->getCommonParticles($refine1['DEF_id'], $refine2['DEF_id']);
		$eulers1 = array();
		foreach ($commonprtls as $k) {
			$eulers1[]=eulerArray(deg2rad($k['euler1_1']), deg2rad($k['euler1_2']), deg2rad($k['rot1']));
		}
		return new Statistics(0,0,0,$r[0]['mean'],0,0,0,$diff,$eulers1,0);
	}

	function getData($reconId, $iter1,$iter2) {
		//query	
		global $particle;
		$r = $particle->getEulerStats($reconId, $iter1, $iter2);
		$diff = explode(",", $r[0]['difference']);

//		print_r($r[0]['eulers']);
//		$eulers = explode(",", $r[0]['eulers']);
//		array_map('toFloat',$diff);
/*
		$refine1 = $particle->getRefinementData($reconId,$iter1);
		$refine2 = $particle->getRefinementData($reconId,$iter2);
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
*/
		/*
		$differences = getDifferences($eulers1,$eulers2);
		$filename= "eulerTests/testFile".$iter1."_".$iter2.".txt";
		$fh = fopen($filename, 'w') or die("can't open file");
		foreach($differences as $i)
		{
			fwrite($fh,$i."\n");
		}
		$myImage = createTriangle($eulers1);
		imagepng($myImage,"eulerTests/testImage".$iter1."_".$iter2.".png");
		fwrite($fh,"Mean: ".$stats->myMean."\n");
		fwrite($fh,"Standard Deviation: ".$stats->myStandardDeviation."\n");
		fwrite($fh,"Min: ".$stats->myMin."\n");
		fwrite($fh,"Max: ".$stats->myMax."\n");
		*/
		return new Statistics(0,0,0,$r[0]['mean'],0,0,0,$diff,$eulers,0);
	//	return $stats;
	}

	function makeTriangle($stats, $outfile="") {
		if (!$outfile)
			header("Content-type: image/x-png");
		$myImage = createTriangle($stats->eulers1);
		echo "Writing to file... ".$outfile."\n";
		imagepng($myImage, $outfile);
	}

	function createGraph($dataset, $outfile="") {
		$graph = new Graph(400,200);
		$graph->SetScale("textlin",0,100);
		$graph->title->set('Euler mean jumps');
		$graph->xaxis->setTitle('Iteration number','middle');
		$graph->yaxis->setTitle('Mean jump','middle');
		$line = new ScatterPlot($dataset);
		$line->linkpoints = true;
	//	$line->SetBarCenter();
		$graph->add($line);
		if (!$outfile)
			header("Content-type: image/x-png");
		$graph->Stroke($outfile);
		echo "Writing to file... ".$outfile."\n";
	}

	echo "\n\n";
?>
