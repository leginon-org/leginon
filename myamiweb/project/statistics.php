<?
require('inc/project.inc.php');
require('inc/experiment.inc.php');

if (privilege('projects') > 2) {
	$title = "Projects";
	login_header($title);
} else {
	redirect(BASE_URL.'accessdeny.php?text=Only superusers and administrators can view this');
}

$useBgcolorOne = TRUE;
$cfg['BgcolorOne']          = '#CCCCCC'; 
$cfg['BgcolorTwo']          = '#DDDDDD';
$byteUnits = array('Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB');
$number_thousands_separator = ',';
$number_decimal_separator = '.';

function formatByteDown($value, $limes = 6, $comma = 0) {
        $dh           = pow(10, $comma);
        $li           = pow(10, $limes);
        $return_value = $value;
        $unit         = $GLOBALS['byteUnits'][0];

        for ( $d = 6, $ex = 15; $d >= 1; $d--, $ex-=3 ) {
            if (isset($GLOBALS['byteUnits'][$d]) && $value >= $li * pow(10, $ex)) {
                $value = round($value / ( pow(1024, $d) / $dh) ) /$dh;
                $unit = $GLOBALS['byteUnits'][$d];
                break 1;
            } // end if
        } // end for

        if ($unit != $GLOBALS['byteUnits'][0]) {
            $return_value = number_format($value, $comma, $GLOBALS['number_decimal_separator'], $GLOBALS['number_thousands_separator']);
        } else {
            $return_value = number_format($value, 0, $GLOBALS['number_decimal_separator'], $GLOBALS['number_thousands_separator']);
        }

        return array($return_value, $unit);
    } // end of the 'formatByteDown' function

function count_tbl_fields($dbc, $table) {
        $res = $dbc->SQLQuery("SHOW FIELDS FROM `$table`");
	$num_rows = mysql_num_rows($res);
	return $num_rows;
}

function count_tbl_rows($dbc, $table) {
        $res = $dbc->SQLQuery("SELECT COUNT(*) FROM `$table`");
        $row = mysql_fetch_row($res);
	$num_rows = $row[0];
	return $num_rows;
}

function getStatistic($db_info) {
	$stats = array(
		'db_name' => $db_info[database],
		'tot_cell' => 0,
		'tbl_cnt' => 0,
		'data_sz' => 0,
		'idx_sz' => 0,
		'tot_sz' => 0
	);
	$legdb = new mysql(DB_HOST, DB_USER, DB_PASS, $db_info[database]);
	$res = $legdb->SQLQuery('SHOW TABLE STATUS FROM `'.$db_info[database].'`'); 
	while ($row = mysql_fetch_array($res, MYSQL_ASSOC)) {
		$stats['tbl_cnt']++;
		$stats['data_sz'] += $row['Data_length'];
		$stats['idx_sz'] += $row['Index_length'];

		$crn=count_tbl_rows($legdb, $row['Name']);
		$cfn=count_tbl_fields($legdb, $row['Name']);
		$ccn=$crn*$cfn;
		$stats['tot_cell'] += $ccn;
        }
	$stats['tot_sz'] = $stats['data_sz'] + $stats['idx_sz'];

	return $stats;
}

function getImageSizeInfo($leg) {
	$info = array();
	$dbp = new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
	$qleg = 'select '
		//.'size as `Size`, dmf as `DMF`, error as `Missing`, experiment as `Online`, '
		.'size as `Size`, experiment as `Online`, '
		.'date_format(timestamp,"%m/%e/%Y") as `updated` '
		.'from project.imagestats where leginon="'.$leg.'" '
		.'order by timestamp desc limit 2';

	$imgsize = $dbp->SQLQuery($qleg);
	while ($row = mysql_fetch_array($imgsize, MYSQL_ASSOC))
		$info[] = $row;

	return $info;
}

$experimentdata = new experimentdata();
$stats = array();
$experiments = array();
$info=array('name'=>'leginon database','host'=>DB_HOST,'database'=>DB_LEGINON);
$experiments[$info[name]] = mysql_num_rows($experimentdata->getExperiments());
$nbimages[$info[name]] = $experimentdata->getNbImages();
$stats[$info[name]] = getStatistic($info);

project_header("Database Statistics");
?>
<h3>
Data Size
</h3>
<table class="tableborder" bgcolor="#FFFFFF" border="0" cellpadding="10" cellspacing="0">
<tr>
<?
foreach ($experiments as $k=>$v) {
echo "<td>";
$title="";
$data="";
$name = array(	
		'leg2' => 'Leginon'
	);
echo "
<h4>$name[$k]</h4>
database name: <b>".$stats[$k][db_name]."</b>
<br>
Image records: <b>$nbimages[$k]</b>
<br>
Experiment records: <b>$experiments[$k]</b>
<p>
Experiment Size/Storage Info:
<table  border=0>";
$displaytitle=true;
foreach (getImageSizeInfo($k) as $imgi ) {
	$data.="<tr>";
	foreach ($imgi as $ki=>$vi) {
	if (eregi('size', $ki)) {
		$vi=number_format($vi)." kB";
	}
	if ($displaytitle) {
		$title .= "<th>$ki</th>";
	}	
	$data  .= '<td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
		.$vi. "\n"
		. '</td>' . "\n";
	}
	$data.="</tr>";
	$displaytitle=false;
	$useBgcolorOne = !$useBgcolorOne;
}
echo "
<tr>$title</tr>
$data
</table>";
echo "</td>";
}
?>
</tr>
</table>
<br>
<font color="#aaaaaa" size=-1>
<b>Note</b>: for a new update, run the command:<br>dbemimgsize --stat
</font>
<h3>
MySQL Database Size
</h3>

<?
       echo '    <table border="0">' . "\n"
       . '        <tr>' . "\n"
       . '            <th>' . "\n"
       . '                &nbsp;';
        echo "\n"
           . 'Database'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th>' . "\n"
           . '                &nbsp;' . "\n"
           . 'Total Cell'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th>' . "\n"
           . '                &nbsp;' . "\n"
           . 'Tables'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th colspan="2">' . "\n"
           . '                &nbsp;' . "\n"
           . 'Data'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th colspan="2">' . "\n"
           . '                &nbsp;' . "\n"
           . 'Indexes'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th colspan="2">' . "\n"
           . '                &nbsp;' . "\n"
           . 'Total'. "\n"
           . '                &nbsp;' . "\n"
           . '            </th>' . "\n";
    echo '        </tr>' . "\n";
    $total_calc = array(
        'db_cnt' => 0,
	'tot_cell' => 0,
        'tbl_cnt' => 0,
        'data_sz' => 0,
        'idx_sz' => 0,
        'tot_sz' => 0
    );
    while (list(, $current) = each($stats)) {
        list($data_size, $data_unit) = formatByteDown($current['data_sz'], 3, 1);
        list($idx_size, $idx_unit)   = formatByteDown($current['idx_sz'], 3, 1);
        list($tot_size, $tot_unit)   = formatByteDown($current['tot_sz'], 3, 1);
        $total_calc['db_cnt']++;
        $total_calc['tot_cell'] += $current['tot_cell'];
        $total_calc['tbl_cnt'] += $current['tbl_cnt'];
        $total_calc['data_sz'] += $current['data_sz'];
        $total_calc['idx_sz'] += $current['idx_sz'];
        $total_calc['tot_sz'] += $current['tot_sz'];
	echo '        <tr>' . "\n";
	echo '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '">' . "\n"
	. '                    ' .$current['db_name'] . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
	. '                ' . $current['tot_cell'] . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
	. '                ' . $current['tbl_cnt'] . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
	. '                ' . $data_size . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '">' . "\n"
	. '                ' . $data_unit . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
	. '                ' . $idx_size . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '">' . "\n"
	. '                ' . $idx_unit . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '" align="right">' . "\n"
	. '                <b>' . "\n"
	. '                    ' . $tot_size . "\n"
	. '                </b>' . "\n"
	. '            </td>' . "\n"
	. '            <td bgcolor="' . ($useBgcolorOne ? $cfg['BgcolorOne'] : $cfg['BgcolorTwo']) . '">' . "\n"
	. '                <b>' . "\n"
	. '                    ' . $tot_unit . "\n"
	. '                </b>' . "\n"
	. '            </td>' . "\n";
	echo '        </tr>' . "\n";
	$useBgcolorOne = !$useBgcolorOne;
    } // end while

        list($data_size, $data_unit) = formatByteDown($total_calc['data_sz'], 3, 1);
        list($idx_size, $idx_unit)   = formatByteDown($total_calc['idx_sz'], 3, 1);
        list($tot_size, $tot_unit)   = formatByteDown($total_calc['tot_sz'], 3, 1);
        echo '        <tr>' . "\n"
           . '            <th>' . "\n"
           . '                &nbsp;Total :&nbsp;' . $total_calc['db_cnt'] . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th align="right">' . "\n"
           . '                &nbsp;' . $total_calc['tot_cell'] . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th align="right">' . "\n"
           . '                &nbsp;' . $total_calc['tbl_cnt'] . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th align="right">' . "\n"
           . '                &nbsp;' . $data_size . "\n"
           . '            </th>' . "\n"
           . '            <th align="left">' . "\n"
           . '                ' . $data_unit . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th align="right">' . "\n"
           . '                &nbsp;' . $idx_size . "\n"
           . '            </th>' . "\n"
           . '            <th align="left">' . "\n"
           . '                ' . $idx_unit . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th align="right">' . "\n"
           . '                &nbsp;' . $tot_size . "\n"
           . '            </th>' . "\n"
           . '            <th align="left">' . "\n"
           . '                ' . $tot_unit . '&nbsp;' . "\n"
           . '            </th>' . "\n"
           . '            <th>&nbsp;</th>' . "\n"
           . '        </tr>' . "\n";
    echo '    </table>' . "\n";
?>
<a href="../totalimagegraph.php?vd=1">[data]</a><br />
<img src="../totalimagegraph.php">
<br />
<a href="../totalimagegraph.php?type=s&vd=1">[data]</a><br />
<img src="../totalimagegraph.php?type=s">
<?
project_footer();
