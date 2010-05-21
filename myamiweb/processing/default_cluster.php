<?php

/**
 * This class allows you to customize your cluster params
 * You can add/modify:
 *    - job file input
 *    - form input
 *    - javascript check
 *
 * Note: each cluster file must be register in config.php
 **/

// For PBS Pro run:
//   pbsnodes -a | egrep "resources_available\.(mem|ncpus)" | sort | uniq -c
// For Torque run:
//   pbsnodes -a | tr ',' '\n' | egrep "(physmem|np)\s*=" | sort | uniq -c
// to get a summary

define('C_NAME', "default_cluster"); // name of cluster, must be single name, e.g., HOST.INSTITUTE.EDU -> HOST

define('C_NODES_DEF', "2");// default number of requested nodes
define('C_NODES_MAX', "8"); // maximum number of requested nodes

define('C_PPN_DEF', "8"); // default processors per node
define('C_PPN_MAX', "8"); // maximum processors per node
define('C_RPROCS_DEF', "8"); // default reconstructions per node, a memory saving option

define('C_WALLTIME_DEF', "240"); // default Wall time in hours
define('C_WALLTIME_MAX', "240"); // maximum Wall time in hours
define('C_CPUTIME_DEF', "240"); // default CPU time in hours
define('C_CPUTIME_MAX', "240"); // maximum CPU time in hours
define('C_MEMORY_MAX', "30"); // maximum memory available per node in gigabytes

define('C_APPION_BIN', ""); // location of appion scripts on cluster, must end in slash, e.g., /usr/local/appion/bin/

class Cluster {

	function set_rootpath($rootpath) {
		$this->rootpath=$rootpath;
	}

	function get_path() {
		return $_POST['outdir'];
	}

	function post_data() {
		
		$stackinfo = explode('|--|',$_POST['stackval']);
	
		# $stackinfo[0] = stackid
		# $stackinfo[1] = pixel size in Angstroms per pixel
		# $stackinfo[2] = stack boxsize (length in either direction) in pixels
		# $stackinfo[3] = number of particles in the stack
		# $stackinfo[4] = appion stackfile path
		# $stackinfo[5] = Imagic stack header file name, including extension but not path
		# $stackinfo[6] = Imagic stack data file name, including extension but not path
		# examples: 
		# $stackinfo[4] = '/your_disk/appion/09aug267/stacks/stack1'
		# $stackinfo[5] = 'start.hed'
		# $stackinfo[6] = 'start.img'
		
		$stackpath=$stackinfo[4];
		$stackname= $stackinfo[5];

		$modelinfo = explode('|--|',$_POST['model']);
		$modelpath = $modelinfo[1];
		$modelname = $modelinfo[2];

		$clusterpath = formatEndPath($_POST['outdir']).$this->rootpath;

		$jobname = $_POST['jobname'];
		$jobfile = "$jobname.job";

		$this->clusterpath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $clusterpath;
		$this->stackname = $stackname;
		$this->jobname = $jobname;
		$this->jobfile = $jobfile;
		$this->clusterfullpath = $this->clusterpath.$jobname;
		$this->stackpath = $stackpath;
		$this->modelpath = $modelpath;
		$this->modelname = $modelname;
		$this->outdir = $_POST['outdir'];
		$this->outfullpath = $this->outdir.$jobname."/";
	}

	function cluster_parameters() {
	}

	function cluster_cmd($host, $user, $pass) {
	}

	function cluster_send_data() {
		$movestr = "";
		$filelist = explode('|--|',$_POST['sendfilelist']);
		foreach ($filelist as $filepath) {
			$path = dirname($filepath);
			$name = basename($filepath);
			$movestr.= "ln -s ".formatEndPath($path)."$name $name\n";
		}
		return $movestr;
	}

	function cluster_receive_data() {
		$movestr = "";
		$outfullpath = $this->outfullpath;
		$filelist = explode('|--|',$_POST['receivefilelist']);
		foreach ($filelist as $filepath) {
			$movestr.= "mv -v $filepath ".formatEndPath($outfullpath)."\n";
		}
		return $movestr;
	}


	function cluster_job_file($jobdata) {
		$clusterfullpath=$this->clusterfullpath;
		$stackpath = $this->stackpath;
		$jobname = $this->jobname;
		$jobfile = $this->jobfile;
		$modelpath = $this->modelpath;
		$modelname = $this->modelname;
		$stackname1 = $this->stackname1;
		$outfullpath = $this->outfullpath;

		$clusterjob.= "#DEBUGGING INFO\n";
		$clusterjob.= "# clusterfull $clusterfullpath\n";
		$clusterjob.= "# jobname     $jobname\n";
		$clusterjob.= "# jobfile     $jobfile\n";
		$clusterjob.= "# outfullpath $outfullpath\n";
		$clusterjob.= "# stackname1  $stackname1\n";
		$clusterjob.= "# stackpath   $stackpath\n";
		$clusterjob.= "# modelname   $modelname\n";
		$clusterjob.= "# modelpath   $modelpath\n";
		$filelist = explode('|--|', $_POST['sendfilelist']);
		foreach ($filelist as $filepath) {
			$clusterjob.= "#   send file   $filepath\n";
		}
		$filelist = explode('|--|', $_POST['receivefilelist']);
		foreach ($filelist as $filepath) {
			$clusterjob.= "#   get file    $filepath\n";
		}
		$clusterjob.= "\n";

		$clusterjob.= "rm -rf $clusterfullpath/recon\n";
		$clusterjob.= "mkdir -p $clusterfullpath/recon\n";
		$clusterjob.= "cd $clusterfullpath/recon\n\n";
		$clusterjob.= "#download files from main filesystem\n";
		$clusterjob.= $this->cluster_send_data();
		$clusterjob.= "setenv RUNPAR_RSH 'ssh'\n\n";

		$clusterjob .= $jobdata;

		$clusterjob.= "#upload files back to main filesystem\n";
		$clusterjob.= $this->cluster_receive_data();
		$clusterjob.= "\ncd $clusterfullpath\n";
		return $clusterjob;
	}

	function cluster_check_msg() {
		$html ="Review your job, and submit.<br/>\n";
		return $html;
	}

	function get_javascript() {
		$js="<script type='text/javascript'>"
			."</script>\n";
		return $js;
	}

	function formatEndPath($path) {
		$path = ereg(DIRECTORY_SEPARATOR."$", $path) ? $path : $path.DIRECTORY_SEPARATOR;
		return $path;
	}

}
$clusterdata = new Cluster();
?>
