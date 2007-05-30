<?php
/**
 *      The Leginon software is Copyright 2003 
 *      The Scripps Research Institute, La Jolla, CA
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 *
 *      Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/project.inc');
require ('inc/particledata.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
require ('inc/ctf.inc');

// IF VALUES SUBMITTED, EVALUATE DATA
if ($_POST['process']) {
        runMakestack();
}

// Create the form page
else {
        createMakestackForm();
}

function createMakestackForm($extra=false, $title='Makestack.py Launcher', $heading='Create an Image Stack') {
        // check if coming directly from a session
        $expId=$_GET['expId'];
	if ($expId){
	        $sessionId=$expId;
		$projectId=getProjectFromExpId($expId);
		$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
	}
	else {
	        $sessionId=$_POST['sessionId'];
	        $formAction=$_SERVER['PHP_SELF'];
	}
	$projectId=$_POST['projectId'];

	// connect to particle and ctf databases
	$particle = new particledata();
	$ctf = new ctfdata();
	$ctfdata=$ctf->hasCtfData($sessionId);
	$prtlrunIds = $particle->getParticleRunIds($sessionId);

	// --- find hosts to run makestack.py
	$hosts=getHosts();

	// --- get list of users
	$users[]=glander;

	// --- make list of file formats
	$fileformats=array('imagic','spider');
	
	$javascript="<script src='js/viewer.js'></script>
        <script LANGUAGE='JavaScript'>
        function enableice(){
          if (document.viewerform.icecheck.checked){
              document.viewerform.ice.disabled=false;
              document.viewerform.ice.value='';
            }
            else {
              document.viewerform.ice.disabled=true;
              document.viewerform.ice.value='0.8';
            }
          }
          function enableace(){
            if (document.viewerform.acecheck.checked){
              document.viewerform.ace.disabled=false;
              document.viewerform.ace.value='';
            }
            else {
              document.viewerform.ace.disabled=true;
              document.viewerform.ace.value='0.8';
            }
          }
          function enableselex(){
            if (document.viewerform.selexcheck.checked){
              document.viewerform.selexon.disabled=false;
              document.viewerform.selexon.value='';
            }
            else {
              document.viewerform.selexon.disabled=true;
              document.viewerform.selexon.value='0.5';
            }
          }
          </SCRIPT>\n";
	
	writeTop($title,$heading,$javascript);
	// write out errors, if any came up:
	if ($extra) {
	        echo "<FONT COLOR='RED'>$extra</FONT>\n<HR>\n";
	}
  
	echo"
       <FORM NAME='viewerform' method='POST' ACTION='$formAction'>\n";
        $sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
        $sessioninfo=$sessiondata['info'];
        if (!empty($sessioninfo)) {
                $sessionpath=$sessioninfo['Image path'];
                $sessionpath=ereg_replace("leginon","appion",$sessionpath);
                $sessionpath=ereg_replace("rawdata","stacks/",$sessionpath);
                $sessionname=$sessioninfo['Name'];
        }

        // Set any existing parameters in form
        $single = ($_POST['single']) ? $_POST['single'] : 'start.hed';
        $runidval = ($_POST['runid']) ? $_POST['runid'] : 'stack1';
        $rundescrval = $_POST['description'];
        $sessionpathval = ($_POST['outdir']) ? $_POST['outdir'] : $sessionpath;
        $prtlrunval = $_POST['prtlrunId'];
        $phasecheck = ($_POST['phaseflip']=='on') ? 'CHECKED' : '';
        $inspectcheck = ($_POST['inspected']=='on') ? 'CHECKED' : '';
        $commitcheck = ($_POST['commit']=='on') ? 'CHECKED' : '';
        $boxszval = $_POST['boxsize'];
	$binval=$_POST['bin'];
        // ice check params
        $iceval = ($_POST['icecheck']=='on') ? $_POST['ice'] : '0.8';
        $icecheck = ($_POST['icecheck']=='on') ? 'CHECKED' : '';
        $icedisable = ($_POST['icecheck']=='on') ? '' : 'DISABLED';
        // ace check params
        $aceval = ($_POST['acecheck']=='on') ? $_POST['ace'] : '0.8';
        $acecheck = ($_POST['acecheck']=='on') ? 'CHECKED' : '';
        $acedisable = ($_POST['acecheck']=='on') ? '' : 'DISABLED';
        // selexon check params
        $selexval = ($_POST['selexcheck']=='on') ? $_POST['selexon'] : '0.5';
        $selexcheck = ($_POST['selexcheck']=='on') ? 'CHECKED' : '';
        $selexdisable = ($_POST['selexcheck']=='on') ? '' : 'DISABLED';
        // density check
	// set to checked by default
        	$invcheck = ($_POST['density']=='invert' || !$_POST['process']) ? 'CHECKED' : '';
        echo"
        <P>
        <TABLE BORDER=0 CLASS=tableborder>
        <TR>
                <TD VALIGN='TOP'>
                <TABLE CELLPADDING='5' BORDER='0'>
                <TR>
                        <TD VALIGN='TOP'>
                        <A HREF=\"javascript:infopopup('runid')\"><B>Stack File Name:</B></A>
                        <INPUT TYPE='text' NAME='single' VALUE='$single'>
                        </TD>
                </TR>
                <TR>
                        <TD VALIGN='TOP'>
                        <A HREF=\"javascript:infopopup('runid')\"><B>Stack Run Name:</B></A>
                        <INPUT TYPE='text' NAME='runid' VALUE='$runidval'>
                        <HR>
                        </TD>
                </TR>
                <TR>
                        <TD VALIGN='TOP'>
                        <B>Stack Description:</B><BR>
                        <TEXTAREA NAME='description' ROWS='3' COLS='36'>$rundescrval</TEXTAREA>
                        </TD>
                </TR>
                <TR>
                        <TD VALIGN='TOP'>         
                        <B>Output Directory:</B><BR>
                        <INPUT TYPE='text' NAME='outdir' VALUE='$sessionpathval' SIZE='38'>
                        </TD>
                </TR>
                <TR>
                        <TD>\n";

        $prtlruns=count($prtlrunIds);

        if (!$prtlrunIds) {
                echo"<FONT COLOR='RED'><B>No Particles for this Session</B></FONT>\n";
        }
        else {
                echo "Particles:
                <SELECT NAME='prtlrunId'>\n";
                foreach ($prtlrunIds as $prtlrun){
                        $prtlrunId=$prtlrun['DEF_id'];
                        $runname=$prtlrun['name'];
                        $prtlstats=$particle->getStats($prtlrunId);
                        $totprtls=commafy($prtlstats['totparticles']);
                        echo "<OPTION VALUE='$prtlrunId'";
                        // select previously set prtl on resubmit
                        if ($prtlrunval==$prtlrunId) echo " SELECTED";
                        echo">$runname ($totprtls prtls)</OPTION>\n";
                }
                echo "</SELECT>\n";
        }
        echo"
                </SELECT>
                </TD>
        </TR>
        <TR>
                <TD VALIGN='TOP'>
                <B>Density:</B><BR>
                <INPUT TYPE='checkbox' NAME='density' $invcheck VALUE='invert'>
                Invert image density<BR>
                </TD>
        </TR>
        <TR>
                <TD>\n";
        if ($ctfdata) echo"<INPUT TYPE='checkbox' NAME='phaseflip' $phasecheck>\nPhaseflip Images<BR>";
        echo"
                <INPUT TYPE='checkbox' NAME='inspected' $inspectcheck>
                Use Inspected Images<BR>
                <INPUT TYPE='checkbox' NAME='commit' $commitcheck>
                Commit to Database<BR>
                </TD>
        </TR>
        <TR>
                <TD VALIGN='TOP'>
                <B>File Format:</B><BR>
                <SELECT NAME='fileformat'>\n";
        foreach($fileformats as $format) {
                $s = ($_POST['fileformat']==$format) ? 'SELECTED' : '';
                echo "<OPTION $s >$format</option>\n";
        }
        echo"
        </TABLE>
        </TD>
        <TD CLASS='tablebg'>
        <TABLE CELLPADDING='5' BORDER='0'>
        <TR>
                <TD VALIGN='TOP'>
                <INPUT TYPE='text' NAME='boxsize' SIZE='5' VALUE='$boxszval'>
                Box Size (Unbinned, in pixels)<BR>
                </TD>
        </TR>
        <TR>
                <TD VALIGN='TOP'>
                <B>Filter Values:</B></A><BR>
                <INPUT TYPE='text' NAME='lp' VALUE='$lpval' DISABLED SIZE='4'>
                <FONT COLOR='grey'>Low Pass</FONT><BR>
                <INPUT TYPE='text' NAME='hp' VALUE='$hpval' DISABLED SIZE='4'>
                <FONT COLOR='grey'>High Pass</FONT><BR>
                <INPUT TYPE='text' NAME='bin' VALUE='$binval' SIZE='4'>
                Binning<BR>
        </TR>
        <TR>
                <TD>
                <INPUT TYPE='checkbox' NAME='icecheck' onclick='enableice(this)' $icecheck>
                Ice Thickness Cutoff<BR>
                Use Ice Thinner Than:<INPUT TYPE='text' NAME='ice' $icedisable VALUE='$iceval' SIZE='4'>
                (between 0.0 - 1.0)
                </TD>
        </TR>\n";
        if ($ctfdata) {
                echo"
        <TR>
                <TD>
                <INPUT TYPE='checkbox' NAME='acecheck' onclick='enableace(this)' $acecheck>
                ACE Confidence Cutoff<BR>
                Use Values Above:<INPUT TYPE='text' NAME='ace' $acedisable VALUE='$aceval' SIZE='4'>
                (between 0.0 - 1.0)
                </TD>
        </TR>\n";
        }
        if ($prtlrunIds) {
                echo"        
        <TR>
                <TD>
                <INPUT TYPE='checkbox' NAME='selexcheck' onclick='enableselex(this)' $selexcheck>
                Particle Correlation Cutoff<BR>
                Use Values Above:<INPUT TYPE='text' NAME='selexon' $selexdisable VALUE='$selexval' SIZE='4'>
                (between 0.0 - 1.0)
                </TD>
        </TR>\n";
        }	
        //if there is CTF data, show min & max defocus range
        if ($ctfdata) {
                $fields = array('defocus1', 'defocus2');
                $bestctf = $ctf->getBestStats($fields, $sessionId);
                $min="-".$bestctf['defocus1'][0]['min'];
                $max="-".$bestctf['defocus1'][0]['max'];
                // check if user has changed values on submit
                $minval = ($_POST['dfmin']!=$min && $_POST['dfmin']!='' && $_POST['dfmin']!='-') ? $_POST['dfmin'] : $min;
                $maxval = ($_POST['dfmax']!=$max && $_POST['dfmax']!='' && $_POST['dfmax']!='-') ? $_POST['dfmax'] : $max;
                echo"
                <TR>
                        <TD VALIGN='TOP'>
                        <B>Defocus Limits</B><BR>
                        <INPUT TYPE='text' NAME='dfmin' VALUE='$minval' SIZE='25'>
                        <INPUT TYPE='hidden' NAME='dbmin' VALUE='$min'>
                        Minimum<BR>
                        <INPUT TYPE='text' NAME='dfmax' VALUE='$maxval' SIZE='25'>
                        <INPUT TYPE='hidden' NAME='dbmax' VALUE='$max'>
                        Maximum
                        </TD>
                </TR>\n";
        }
        echo"
                </SELECT>
                </TD>
        </TR>
        </TABLE>
        </TD>
        </TR>
        <TR>
                <TD COLSPAN='2' ALIGN='CENTER'>
                <HR>
                Host: <select name='host'>\n";
        foreach($hosts as $host) {
                $s = ($_POST['host']==$host) ? 'selected' : '';
                echo "<option $s >$host</option>\n";
        }
        echo "</select>
        User: <select name='user'>\n";
        foreach($users as $user) {
                $s = ($_POST['user']==$user) ? 'selected' : '';
                echo "<option $s >$user</option>\n";
        }
	echo"
          </select>
          <BR>
          <input type='submit' name='process' value='Create Stack'><BR>
          <FONT COLOR='RED'>Submission will NOT create a stack, only output a command that you can copy and paste into a unix shell</FONT>
          </TD>
        </TR>
        </TABLE>
        </FORM>
        </CENTER>\n";
	writeBottom();
}

function runMakestack() {
        $host = $_POST['host'];
        $user = $_POST['user'];
 
        $single=$_POST['single'];
        $runid=$_POST['runid'];

        //make sure a session was selected
        $description=$_POST['description'];
        if (!$description) {
                createMakestackForm("<B>ERROR:</B> Enter a brief description of the stack");
                exit;
        }

        //make sure a session was selected
        $outdir=$_POST['outdir'];
        if (!$outdir) {
                createMakestackForm("<B>ERROR:</B> Select an experiment session");
                exit;
        }
        // make sure outdir ends with '/'
        if (substr($outdir,-1,1)!='/') $outdir.='/';

        // get selexon runId
        $prtlrunId=$_POST['prtlrunId'];
        if (!$prtlrunId) {
                createMakestackForm("<B>ERROR:</B> No particle coordinates in the database");
                exit;
        }
        
        $invert = ($_POST['density']=='invert') ? '' : 'noinvert';
        $phaseflip = ($_POST['phaseflip']=='on') ? 'phaseflip' : '';
        $inspected = ($_POST['inspected']=='on') ? 'inspected' : '';
        $commit = ($_POST['commit']=="on") ? 'commit' : '';
	// binning amount
	$bin=$_POST['bin'];
	if ($bin) {
	        if (!is_numeric($bin)) {
		        createMakestackForm("<B>ERROR:</B> Binning amount must be 2, 4, 8, 16, 32...");
			exit;
		}
	}

        // box size
        $boxsize = $_POST['boxsize'];
        if (!$boxsize) {
                createMakestackForm("<B>ERROR:</B> Specify a box size");
                exit;
        }
        if (!is_numeric($boxsize)) {
                createMakestackForm("<B>ERROR:</B> Box size must be an integer");
                exit;
        }

        // ace cutoff
        if ($_POST['acecheck']=='on') {
                $ace=$_POST['ace'];
                if ($ace > 1 || $ace < 0 || !$ace) {
                        createMakestackForm("<B>ERROR:</B> Ace cutoff must be between 0 & 1");
                        exit;
                }
        }

        // selexon cutoff
        if ($_POST['selexcheck']=='on') {
                $selexon=$_POST['selexon'];
                if ($selexon > 1 || $selexon < 0 || !$selexon) {
                        createMakestackForm("<B>ERROR:</B> Selexon cutoff must be between 0 & 1");
                        exit;
                }
        }

        // check defocus cutoffs
        $dfmin = ($_POST['dfmin']==$_POST['dbmin']) ? '' : $_POST['dfmin'];
        $dfmax = ($_POST['dfmax']==$_POST['dbmax']) ? '' : $_POST['dfmax'];

        $fileformat = ($_POST['fileformat']=='spider') ? 'spider' : '';

//        $command ="source /ami/sw/ami.csh;";
//        $command.="source /ami/sw/share/python/usepython.csh common32;";
//        $command.="source /home/$user/pyappion/useappion.csh;";
        $command.="makestack.py ";
        $command.="single=$single ";
        $command.="runid=$runid ";
        $command.="outdir=$outdir ";
        $command.="prtlrunId=$prtlrunId ";
        if ($invert) $command.="noinvert ";
        if ($phaseflip) $command.="phaseflip ";
        if ($inspected) $command.="inspected ";
        if ($commit) $command.="commit ";
        $command.="boxsize=$boxsize ";
	if ($bin) $command.="bin=$bin ";
        if ($ace) $command.="ace=$ace ";
        if ($selexon) $command.="selexonmin=$selexon ";
        if ($dfmin) $command.="mindefocus=$dfmin ";
        if ($dfmax) $command.="maxdefocus=$dfmax ";
        if ($fileformat) $command.="spider ";
        $command.="description=\"$description\"";

        $cmd = "exec ssh $user@$host '$command > makestacklog.txt &'";
//        exec($cmd ,$result);

        writeTop("Makestack Run","Makestack Params");

        echo"
        <P>
        <TABLE WIDTH='600' BORDER='1'>
        <TR><TD COLSPAN='2'>
        <B>Makestack Command:</B><BR>
        $command
        </TD></TR>
        <TR><TD>stack name</TD><TD>$single</TD></TR>
        <TR><TD>runid</TD><TD>$runid</TD></TR>
        <TR><TD>outdir</TD><TD>$outdir</TD></TR>
        <TR><TD>description</TD><TD>$description</TD></TR>
        <TR><TD>selexonId</TD><TD>$prtlrunId</TD></TR>
        <TR><TD>invert</TD><TD>$invert</TD></TR>
        <TR><TD>phaseflip</TD><TD>$phaseflip</TD></TR>
        <TR><TD>inspected</TD><TD>$inspected</TD></TR>
        <TR><TD>commit</TD><TD>$commit</TD></TR>
        <TR><TD>box size</TD><TD>$boxsize</TD></TR>
        <TR><TD>binning</TD><TD>$bin</TD></TR>
        <TR><TD>ace cutoff</TD><TD>$ace</TD></TR>
        <TR><TD>selexon cutoff</TD><TD>$selexon</TD></TR>
        <TR><TD>minimum defocus</TD><TD>$dfmin</TD></TR>
        <TR><TD>maximum defocus</TD><TD>$dfmax</TD></TR>
        <TR><TD>spider</TD><TD>$fileformat</TD></TR>
        </TABLE>\n";
        writeBottom();
}
?>
