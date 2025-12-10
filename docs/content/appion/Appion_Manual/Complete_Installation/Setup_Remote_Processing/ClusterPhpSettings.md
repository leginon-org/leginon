A list of variables to set in your_cluster.php.

## Introduction

These are variables you need to set in your_cluster.php that you create based on default_cluster.php we provide. The example in default_cluster.php should work if the appion processing disk can be accessed directly from the cluster.

Each define(var,value) sets up a number shown in your emanJobGen.php or restricts the value you can put there so that you do not accidentally set impossible numbers for your cluster when you use the form to submit the job in the future.

## Details

Most variables end with _DEF or _MAX where _DEF means default values shows up in the webform and _MAX means the physical limit, normally defined by your cluster machine. Therefore, the web form will complain if you set a number larger than that.

**C_NAME** means cluster name.

**C_NODES** means number of nodes used by your job.

**C_PPN_DEF** means default number of processors per node show up on the web form as default

**C_PPN_MAX** means maximal number of processors per node

**C_RPOCS_DEF** means default number of processors per node the web will force if you did not specify how many nodes you want to use per node. This is most likely either equal to C_PPN_MAX or C_PPN_DEF if you don't want people waste processors. We recommend setting C_RPOCS_DEF to C_PPN_MAX.

**C_WALLTIME** (in hours) means the maximal real time your job is allowed to run. If your cluster is configured properly, it would suspend the job after that so that it does not delay others.

**C_CPUTIME** (in hours) means the maximal cpu time your job is allowed to run.
