<?php

/**
 * This class allows you to customize your cluster params
 * You can add/modify:
 *    - job file input
 *    - form input
 *    - javascript check
 *
 * Note: each cluster file must be register in config_processing.php
 **/
	
define('C_NAME', "default_cluster");

define('C_NODES_DEF', "2");
define('C_NODES_MAX', "8");

define('C_PPN_DEF', "8");
define('C_PPN_MAX', "8");
define('C_RPROCS_DEF', "8");

define('C_WALLTIME_DEF', "240"); //in hours
define('C_WALLTIME_MAX', "240"); //in hours
define('C_CPUTIME_DEF', "240"); //in hours
define('C_CPUTIME_MAX', "240"); //in hours
define('C_MEMORY_MAX', "30"); //in GB

define('C_APPION_BIN', ""); //ends in slash, example, /usr/local/appion/bin/

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
			$movestr.= "mv $filepath ".formatEndPath($outfullpath)."\n";
		}
		return $movestr;
	}


	function cluster_job_file($job) {
		$clusterfullpath=$this->clusterfullpath;
		$stackpath = $this->stackpath;
		$modelpath = $this->modelpath;
		$modelname = $this->modelname;
		$stackname = $this->stackname;

		$clusterjob= "rm -rf $clusterfullpath/recon\n";
		$clusterjob.= "mkdir -p $clusterfullpath/recon\n";
		$clusterjob.= "cd $clusterfullpath/recon\n\n";
		$clusterjob.= $this->cluster_send_data();
		$clusterjob.= "setenv RUNPAR_RSH 'ssh'\n\n";

		$clusterjob .= $job;

		$clusterjob.= $this->cluster_receive_data();
		$clusterjob.= "\ncd $clusterfullpath\n";
		$clusterjob.= "\nrm -rf $clusterfullpath/recon\n";
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
