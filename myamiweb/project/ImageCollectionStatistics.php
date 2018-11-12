<?php

require_once('../config.php');


date_default_timezone_set('America/New_York');

$query = "SELECT a.`DEF_timestamp` as timestamp FROM `CameraEMData` b
INNER JOIN `AcquisitionImageData` a
ON b.`DEF_ID` = a.`REF|CameraEMData|camera` 
WHERE b.`align frames` = 0";



 echo $query."<br><br>";

 $conn_leginon = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_LEGINON);
 
 
 $results = $conn_leginon->query($query);
 
 
echo 'results : <br><br>';
print_r($conn_leginon);
echo '<br><br>';
$i = 0;
  while ($row = $results->fetch_array(MYSQLI_ASSOC))
 
 {
    
    $data[$i] = new DateTime($row['timestamp']);
   
    $i++;
 }
 
 $jan = 0;
 $feb = 0;
 $mar = 0;
 $apr = 0;
 $may = 0;
 $jun = 0;
 $jul = 0;
 $aug = 0;
 $sep = 0;
 $oct = 0;
 $nov = 0;
 $dec = 0;
 $total = 0;
 
 echo "Images collected by month: <br><br>";
 for($i=0;$i<count($data);$i++)
 {
    
    $total++;
    if(($data[$i]<(new DateTime("2015-02-01"))))
    {
        $jan++;
    }
    
    if(($data[$i]>=(new DateTime("2015-02-01"))) && ($data[$i]<(new DateTime("2015-03-01"))))
    {
        $feb++;
    }
    if(($data[$i]>=(new DateTime("2015-03-01"))) && ($data[$i]<(new DateTime("2015-04-01"))))
    {
        $mar++;
    }
    if(($data[$i]>=(new DateTime("2015-04-01"))) && ($data[$i]<(new DateTime("2015-05-01"))))
    {
        $apr++;
    }
    if(($data[$i]>=(new DateTime("2015-05-01"))) && ($data[$i]<(new DateTime("2015-06-01"))))
    {
        $may++;
    }
    if(($data[$i]>=(new DateTime("2015-06-01"))) && ($data[$i]<(new DateTime("2015-07-01"))))
    {
        $jun++;
    }
    if(($data[$i]>=(new DateTime("2015-07-01"))) && ($data[$i]<(new DateTime("2015-08-01"))))
    {
        $jul++;
    }
    if(($data[$i]>=(new DateTime("2015-08-01"))) && ($data[$i]<(new DateTime("2015-09-01"))))
    {
        $aug++;
    }
    if(($data[$i]>=(new DateTime("2015-09-01 00:00:00"))) && ($data[$i]<(new DateTime("2015-10-01"))))
    {
        $sep++;
    }
    
   
 
 
 
 }
 
 echo "Total : ".$total."<br><br>";
 echo "Jan : ".$jan."<br>";
 echo "Feb : ".$feb."<br>";
 echo "Mar : ".$mar."<br>";
 echo "Apr : ".$apr."<br>";
 echo "May : ".$may."<br>";
 echo "Jun : ".$jun."<br>";
 echo "Jul : ".$jul."<br>";
 echo "Aug : ".$aug."<br>";
 echo "Sep : ".$sep."<br><br>";
 
 echo "Total Check : ".($jan+$feb+$mar+$apr+$may+$jun+$jul+$aug+$sep)."<br><br>";
 
 $monthly[0] = $jan;
 $monthly[1] = $feb;
 $monthly[2] = $mar;
 $monthly[3] = $apr;
 $monthly[4] = $may;
 $monthly[5] = $jun;
 $monthly[6] = $jul;
 $monthly[7] = $aug;
 $monthly[8] = $sep;
 
   
 
 $jan = 0;
 $feb = 0;
 $mar = 0;
 $apr = 0;
 $may = 0;
 $jun = 0;
 $jul = 0;
 $aug = 0;
 $sep = 0;
 $oct = 0;
 $nov = 0;
 $dec = 0;
 $total = 0;
 
 
 echo "Cumulative images collected by month: <br><br>";
 for($i=0;$i<count($data);$i++)
 {
    
    $total++;
    if(($data[$i]<(new DateTime("2015-02-01"))))
    {
        $jan++;
    }
    
    if(($data[$i]<(new DateTime("2015-03-01"))))
    {
        $feb++;
    }
    if(($data[$i]<(new DateTime("2015-04-01"))))
    {
        $mar++;
    }
    if(($data[$i]<(new DateTime("2015-05-01"))))
    {
        $apr++;
    }
    if(($data[$i]<(new DateTime("2015-06-01"))))
    {
        $may++;
    }
    if(($data[$i]<(new DateTime("2015-07-01"))))
    {
        $jun++;
    }
    if(($data[$i]<(new DateTime("2015-08-01"))))
    {
        $jul++;
    }
    if(($data[$i]<(new DateTime("2015-09-01"))))
    {
        $aug++;
    }
    if(($data[$i]<(new DateTime("2015-10-01"))))
    {
        $sep++;
    }
    
   

 
 
 }
 

 echo "Jan : ".$jan."<br>";
 echo "Feb : ".$feb."<br>";
 echo "Mar : ".$mar."<br>";
 echo "Apr : ".$apr."<br>";
 echo "May : ".$may."<br>";
 echo "Jun : ".$jun."<br>";
 echo "Jul : ".$jul."<br>";
 echo "Aug : ".$aug."<br>";
 echo "Sep : ".$sep."<br><br>";
 
 $cumulative[0] = $jan;
 $cumulative[1] = $feb;
 $cumulative[2] = $mar;
 $cumulative[3] = $apr;
 $cumulative[4] = $may;
 $cumulative[5] = $jun;
 $cumulative[6] = $jul;
 $cumulative[7] = $aug;
 $cumulative[8] = $sep;
 
 
 
 ?>

