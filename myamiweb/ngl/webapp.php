<?php
require_once "../config.php";
require_once '../inc/login.inc';

if (! $dbemauth->is_logged()) {
	$redirect=$_SERVER['REQUEST_URI'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$filename=$_GET['filename'];

if (empty($filename)) {
	return;
}
$expId = $_GET['expId'];
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <title>NGL - webapp</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, user-scalable=no, minimum-scale=1.0, maximum-scale=1.0">
    <link rel="stylesheet" href="css/font-awesome.min.css" />
    <link rel="stylesheet" href="css/main.css" />
    <link rel="subresource" href="css/light.css" />
    <link rel="subresource" href="css/dark.css" />
</head>
<body>
    <!-- NGL -->
    <script src="js/ngl.js"></script>

    <!-- UI -->
    <script src="js/lib/signals.min.js"></script>
    <script src="js/lib/tether.min.js"></script>
    <script src="js/lib/colorpicker.min.js"></script>
    <script src="js/ui/ui.js"></script>
    <script src="js/ui/ui.extra.js"></script>
    <script src="js/ui/ui.ngl.js"></script>
    <script src="js/gui.js"></script>

    <!-- EXTRA -->
    <script src="js/plugins.js"></script>

    <script>
        NGL.cssDirectory = "css/";
        var stage;
        document.addEventListener( "DOMContentLoaded", function(){
            stage = new NGL.Stage();
            NGL.StageWidget( stage );
            var oReq = new XMLHttpRequest();
            oReq.open("GET", "../processing/download.php?expId=<?php echo $expId  ?>&file=<?php echo $filename  ?>", true);
            oReq.responseType = "arraybuffer";
            var infoText = new UI.Text( "Loading..." );
            NGL.sidebar.add( infoText );
            
            oReq.onload = function(oEvent) {
              var blob = new Blob([oReq.response],  { type: 'application/octet-binary'} );
              var filename = '<?php echo $filename  ?>'.replace(/^.*[\\\/]/, '')
              stage.loadFile(blob, {ext: 'mrc', name: filename}).then(function (component) {
            	  component.addRepresentation("surface");
            	  NGL.sidebar.remove( infoText );
            	  component.autoView();
            	});
              
            };

            oReq.send();
            
            
            
            } );            

    </script>
</body>
</html>
