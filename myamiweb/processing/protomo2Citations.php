<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();

$html = "<h3><center><b>Citations for Appion-Protomo and Integrated Software/Techniques</b></center></h3><br>";

$html .= "<hr><center><b>If you use Appion-Protomo for any purpose, you must cite the following</b></center></hr><br><br>";

$html .= "Accurate marker-free alignment with simultaneous geometry determination and reconstruction of tilt series in electron tomography<br>";
$html .= "Winkler H, Taylor KA<br>";
$html .= '<a href="https://doi.org/10.1016/j.ultramic.2005.07.007" target="_blank">doi:10.1016/j.ultramic.2005.07.007</a><br><br>';

$html .= "Automated batch fiducial-less tilt-series alignment in Appion using Protomo<br>";
$html .= "Alex J. Noble, Scott M. Stagg<br>";
$html .= '<a href="https://doi.org/10.1016/j.jsb.2015.10.003" target="_blank">doi:10.1016/j.jsb.2015.10.003</a><br><br>';

$html .= "Appion: an integrated, database-driven pipeline to facilitate EM image processing<br>";
$html .= "Lander GC, Stagg SM, Voss NR, et al.<br>";
$html .= '<a href="https://doi.org/10.1016/j.jsb.2009.01.002" target="_blank">doi:10.1016/j.jsb.2009.01.002</a><br>';

$html .= "<br><hr><center><b>If you dose compensated your images in Appion-Protomo, you must cite the following</b></center></hr><br><br>";

$html .= "Measuring the optimal exposure for single particle cryo-EM using a 2.6 angstrom reconstruction of rotavirus VP6<br>";
$html .= "Timothy Grant, Nikolaus Grigorieff<br>";
$html .= '<a href="https://doi.org/10.7554/eLife.06980" target="_blank">doi:10.7554/eLife.06980</a><br>';

$html .= "<br><hr><center><b>If you used TomoCTF to estimate defocus and/or to correct for CTF, you must cite the following</b></center></hr><br><br>";

$html .= "CTF Determination and Correction in Electron Cryotomography<br>";
$html .= "J.J. Fernandez, S. Li, R.A. Crowther<br>";
$html .= '<a href="https://doi.org/10.1016/j.ultramic.2006.02.004" target="_blank">doi:10.1016/j.ultramic.2006.02.004</a><br>';

$html .= "<br><hr><center><b>If you used IMOD's ctfphaseflip to correct for CTF, you must cite the following</b></center></hr><br><br>";

$html .= "CTF determination and correction for low dose tomographic tilt series<br>";
$html .= "Quanren Xiong, Mary K. Morphew, Cindi L. Schwartz, Andreas H. Hoenger, David N. Mastronarde<br>";
$html .= '<a href="https://doi.org/10.1016/j.jsb.2009.08.016" target="_blank">doi:10.1016/j.jsb.2009.08.016</a><br>';

$html .= "<br><hr><center><b>If you used Tomo3D to generate a reconstruction, you must cite the following</b></center></hr><br><br>";

$html .= "Fast tomographic reconstruction on multicore computers<br>";
$html .= "J.I. Agulleiro, J.J. Fernandez<br>";
$html .= '<a href="https://doi.org/10.1093/bioinformatics/btq692" target="_blank">doi:10.1093/bioinformatics/btq692</a><br><br>';

$html .= "Tomo3D 2.0 - Exploitation of Advanced Vector eXtensions (AVX) for 3D reconstruction<br>";
$html .= "J.I. Agulleiro, J.J. Fernandez<br>";
$html .= '<a href="https://doi.org/10.1016/j.jsb.2014.11.009" target="_blank">doi:10.1016/j.jsb.2014.11.009</a><br>';

$html .= "<br><hr><center><b>If you used Appion-Protomo to investigate single particle grids, you may wish to cite the following</b></center></hr><br><br>";

$html .= "Routine Single Particle CryoEM Sample and Grid Characterization by Tomography<br>";
$html .= "Noble, A. J., Dandey, V. P., Wei, H., Brasch, J., Chase, J., Acharya, P., Tan Y. Z., Zhang Z., Kim L. Y., Scapin G., Rapp M., Eng E. T., Rice M. J., Cheng A., Negro C. J., Shapiro L., Kwong P. D., Jeruzalmi D., des Georges A., Potter C. S., Carragher, B.<br>";
$html .= '<a href="https://doi.org/10.1101/230276" target="_blank">doi:10.1101/230276</a><br><br>';

echo $html;

?>