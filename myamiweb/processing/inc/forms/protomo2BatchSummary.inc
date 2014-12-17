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
$iters=$_SESSION['iters'];
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
		
		$corrpeak_files = glob("$outdir/$runname/gifs/correlations/s*.gif");
		$rec_files = glob("$outdir/$runname/gifs/reconstructions/s*.gif");
		
		// Horizontal table of all of the correlation peaks for easy identification of bad alignment iterations
		$i = 0;
		$html .= '<table id="" class="display" cellspacing="0" border="1" width="100%">';
		foreach ($corrpeak_files as $corr)
		{
			$ite=$i+1;
			$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_files[$i];
			$html .= "Iteration #".$ite;
			$html .= '<td><center><img src="'.$corrpeak_gif.'"></td>';
			$i++;
		}
		$html .= '</tr><tr></table>';
		
		// Display Refinement for final iteration of each Tilt Series
		for ($i = 0; $i < max(count($corrpeak_files),count($rec_files)); $i++)
		{
			$ite=$i+1;
			$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_files[$i];
			$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_files[$i];
			$html .= "
		<hr />
		<center><H3><b>Refinement Iteration #$ite</b></H3></center>
		<hr />";
			$html .= "
		<br />
		<center><H4>Tilt Series Correlation Peaks</H4></center>
		<br />";
			if (isset($corrpeak_files[$i])) {
				$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /><br /><hr /></center>";
			} else {
				$html .= "<b>Depiction Correlation Peak Gif for Iteration $ite either failed to generate or is still processing</b>";
			}
			$html .= "
		<br />
		<center><H4>Tilt Series Preliminary Reconstruction After Refinement</H4></center>
		<br />";
			if (isset($rec_files[$i])) {
				$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" /></center>'."<br /><br />";
			} else {
				$html .= "<center><b>Depiction Reconstruction Gif for Iteration $ite either failed to generate or is still processing</b></center>";
			}
		}
		
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
