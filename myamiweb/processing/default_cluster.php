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
	
define(C_NAME, "default_cluster");

define(C_NODES_DEF, "2");
define(C_NODES_MAX, "8");

define(C_PPN_DEF, "8");
define(C_PPN_MAX, "8");
define(C_RPROCS_DEF, "8");

define(C_WALLTIME_DEF, "240");
define(C_WALLTIME_MAX, "240");
define(C_CPUTIME_DEF, "240");
define(C_CPUTIME_MAX, "240");

define(C_APPION_BIN, "");

class Cluster {

	function set_rootpath($rootpath) {
		$this->rootpath=$rootpath;
	}

	function get_path() {
		return $_POST['outdir'];
	}

	function post_data() {
		
		$stackinfo = explode('|--|',$_POST['stackval']);
		$stackpath=$stackinfo[3];
		$stackname1=$stackinfo[5];
		$stackname2=$stackinfo[5];

		$modelinfo = explode('|--|',$_POST['model']);
		$modelpath = $modelinfo[1];
		$modelname = $modelinfo[2];

		$clusterpath = formatEndPath($_POST['outdir']).$this->rootpath;

		$jobname = $_POST['jobname'];
		$jobfile = "$jobname.job";

		$this->clusterpath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $clusterpath;
		$this->stackname1 = $stackname2;
		$this->stackname2 = $stackname2;
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

	function cluster_job_file($job) {
		$clusterfullpath=$this->clusterfullpath;
		$stackpath = $this->stackpath;
		$modelpath = $this->modelpath;
		$modelname = $this->modelname;
		$stackname1 = $this->stackname1;

		$clusterjob= "rm -rf $clusterfullpath/recon\n";
		$clusterjob.= "mkdir -p $clusterfullpath/recon\n";
		$clusterjob.= "cd $clusterfullpath/recon\n\n";
		$ext=strrchr($stackname1,'.');
		$stackname=substr($stackname1,0,-strlen($ext));
		$clusterjob.= "ln -s $stackpath/$stackname.hed start.hed\n";
		$clusterjob.= "ln -s $stackpath/$stackname.img start.img\n";
		$clusterjob.= "ln -s $modelpath/$modelname threed.0a.mrc\n";
		$clusterjob.= "setenv RUNPAR_RSH 'ssh'\n\n";

		$clusterjob .= $job;

		$clusterjob.= "\nmv $clusterfullpath/recon/* $clusterfullpath/.\n";
		$clusterjob.= "\nmv $clusterfullpath/recon/.* $clusterfullpath/.\n";
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

}
$clusterdata = new Cluster();
?>
