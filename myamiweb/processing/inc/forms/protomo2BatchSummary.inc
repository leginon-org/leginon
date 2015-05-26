<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2BatchSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML )
	{
		parent::__construct($expId, $extraHTML);
		print "_POST:" . "<br>";
		var_dump($_POST);
		print "_GET:" . "<br>";
		var_dump($_GET);
		print "_SESSION:" . "<br>";
		var_dump($_SESSION);
		
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Batch Summary' );
		$this->setHeading( 'Protomo Batch Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
	}
	
	// Display plots and gifs
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $outdir;
		global $runname;
		$trimmed_runname=preg_replace("/\d+$/","",$runname).'0001';
		print $trimmed_runname;
		$test= glob("$outdir/$trimmed_runname/media/correlations/s*.mp4");
		print $test;
		foreach (glob("$outdir/$trimmed_runname/media/correlations/s*.mp4") as $filename){
			print $filename."<br />";
		}
		$rec_files = glob("$outdir/$runname/media/reconstructions/s*.gif");
		
		// Table of all of the correlation peaks for easy identification of bad alignment iterations
		$html .= "
	<hr />
	<center><H4><b>Best Iteration Correlation Peak for Each Tilt Series ".docpop('corrimageinfo_refine', '(Info)')."</b></H4></center>
	<hr />";
		
		$i = 0;
		$j = -1;
		$html .= '<table id="" class="display" cellspacing="0" border="1" width="100%">';
		$html .= "<tr>";
		if (count($corrpeak_files) > 0)
		{
		do {
			foreach ($corrpeak_files as $corr)
			{
				$ite=$i+1;
				if ($ite <= count($corrpeak_files) AND $ite > 0) {
					$html .= '<th><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">Tilt Series #'.$ite.'</a></th>';
				}
				if ($ite % 4 == 0 OR $ite < 1) {
					$html .= "</tr><tr>";
					$j++;
					break;
				}
				$i++;
			}
			$i = 0 + 4*$j;
			foreach ($corrpeak_files as $corr)
			{
				$ite=$i+1;
				if ($ite <= count($corrpeak_files) AND $ite > 0) {
					$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_files[$i];
					$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
				}
				if ($ite % 4 == 0 OR $ite < 1) {
					$html .= "</tr><tr>";
					$i++;
					break;
				}
				$i++;
			}
		} while ($i < count($corrpeak_files));
		}
		$html .= '</tr><tr></table><br>';
		
		
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment result in the final iteration] <font size='5'>→</font></center></b></a>";
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
		
		return $html;
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $iters;
		global $imageinfo;

		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['iters'] = $iters;
		$_SESSION['imageinfo'] = $imageinfo;

		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment result in the final iteration] <font size='5'>→</font></center></b></a>";
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
		
		return $html;
	}
}
?>
