<?php
$filename=$_GET['filename'];

if (empty($filename)) {
	return;
}
$expId = $_GET['expId'];
?>

<!DOCTYPE HTML>
<html>
  <head>
    <title>WebViewer</title>
<!-- from  http://alecjacobson.com/programs/webviewer/ -->
    <script src="../js/3dviewer/mesh_request.js" type="text/javascript"></script>
    <script src="../js/3dviewer/gl-matrix.js" type="text/javascript"></script>
    <script src="../js/3dviewer/epsilon.js" type="text/javascript"></script>
    <script src="../js/3dviewer/trackball.js" type="text/javascript"></script>
    <script src="../js/3dviewer/findpos.js" type="text/javascript"></script>
    <script src="../js/3dviewer/per_face_normals.js" type="text/javascript"></script>
    <script src="../js/3dviewer/per_vertex_normals.js" type="text/javascript"></script>
    <script src="../js/3dviewer/getUnique.js" type="text/javascript"></script>
    <script src="../js/3dviewer/remove_unreferenced.js" type="text/javascript"></script>
<!--     <script src="../js/3dviewer/stats.js" type="text/javascript"></script> -->
    <script src="../js/3dviewer/webgl-debug.js" type="text/javascript"></script>
    <script src="../js/3dviewer/webgl-utils.js" type="text/javascript"></script>
    <script src="../js/3dviewer/readOBJ.js" type="text/javascript"></script>
    <script src="../js/3dviewer/webviewer.js" type="text/javascript"></script>
    <!-- For now put shaders here, but eventually should be loaded by request:
    http://stackoverflow.com/questions/4878145/javascript-and-webgl-external-scripts
    -->
    <script id="per-fragment-lighting-fs" type="x-shader/x-fragment">
precision mediump float;

varying vec2 vTextureCoord;
varying vec3 vTransformedNormal;
varying vec4 vPosition;

uniform float uMaterialShininess;

uniform bool uShowSpecularHighlights;
uniform bool uUseLighting;
uniform bool uUseTextures;

uniform vec3 uAmbientColor;

uniform vec3 uPointLightingLocation;
uniform vec3 uPointLightingSpecularColor;
uniform vec3 uPointLightingDiffuseColor;

uniform sampler2D uSampler;


void main(void) {
    vec3 lightWeighting;
    if (!uUseLighting) {
        lightWeighting = vec3(1.0, 1.0, 1.0);
    } else {
        //vec3 lightDirection = normalize(uPointLightingLocation - vPosition.xyz);
        vec3 lightDirection = vec3(0,0,1);
        vec3 normal = normalize(vTransformedNormal);

        float specularLightWeighting = 0.0;
        if (uShowSpecularHighlights) {
            vec3 eyeDirection = normalize(-vPosition.xyz);
            vec3 reflectionDirection = reflect(-lightDirection, normal);

            specularLightWeighting = pow(max(dot(reflectionDirection, eyeDirection), 0.0), uMaterialShininess);
        }

        float diffuseLightWeighting = max(dot(normal, lightDirection), 0.0);
        lightWeighting = uAmbientColor
            + uPointLightingSpecularColor * specularLightWeighting
            + uPointLightingDiffuseColor * diffuseLightWeighting;
    }

    vec4 fragmentColor;
    if (uUseTextures) {
        fragmentColor = texture2D(uSampler, vec2(vTextureCoord.s, vTextureCoord.t));
    } else {
        fragmentColor = vec4(1.0, 1.0, 1.0, 1.0);
    }
    gl_FragColor = vec4(fragmentColor.rgb * lightWeighting, fragmentColor.a);
}
    </script>

    <script id="per-fragment-lighting-vs" type="x-shader/x-vertex">
attribute vec3 aVertexPosition;
attribute vec3 aVertexNormal;
attribute vec2 aTextureCoord;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;
uniform mat3 uNMatrix;

varying vec2 vTextureCoord;
varying vec3 vTransformedNormal;
varying vec4 vPosition;


void main(void) {
    vPosition = uMVMatrix * vec4(aVertexPosition, 1.0);
    gl_Position = uPMatrix * vPosition;
    vTextureCoord = aTextureCoord;
    vTransformedNormal = uNMatrix * aVertexNormal;
}
    </script>

  </head>

  <body>
  <canvas id="webviewer_canvas" style="width:690px;"></canvas>
  
   <div id="loadingtext" style='font-family:"Chalkduster",sans-serif;background-color:#FFF;'></div>
<script>
function webGLStart(canvas_id,error_id) {
//   init_stats();
  
  var canvas = document.getElementById(canvas_id);
  //init_drag_and_drop(canvas);
  loading = document.getElementById("loadingtext");
  init_mouse(canvas);
  setupCanvasMousing(canvas);
  initGL(canvas);
  initShaders();
  //initTextures();
  setTimeout(function() {
	loading.textContent = "Loading remote OBJ...";
	loading.style.backgroundColor = "#5f4";	  
    readOBJ_from_server('download.php?expId=<?php echo $expId  ?>&file=<?php echo $filename  ?>',mesh, function(mesh)
    {
    	setTimeout(function(){handleLoadedMesh(mesh);loading.textContent="";},0);
        loading.textContent = "Handling OBJ...";
        loading.style.backgroundColor = "#fab";    	
    });
  },50);

  gl.enable(gl.DEPTH_TEST);

  tick();
}

webGLStart("webviewer_canvas","webviewer_error");

</script>
  
  </body>
</html>
