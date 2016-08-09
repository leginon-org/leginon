// Compute face normals via vertex position list, face list
// Inputs:
//   V  #V by 3 eigen Matrix of mesh vertex 3D positions
//   F  #F by 3 eigne Matrix of face (triangle) indices
// Output:
//   N  #F by 3 eigen Matrix of mesh face (triangle) 3D normals
function per_face_normals(V,F)
{
  var N = new Array(F.length);
  // loop over faces
  for(var f = 0;f<F.length/3;f++)
  {
    var e01 = vec3.fromValues(
      V[F[3*f+1]*3+0] - V[F[3*f+0]*3+0],
      V[F[3*f+1]*3+1] - V[F[3*f+0]*3+1],
      V[F[3*f+1]*3+2] - V[F[3*f+0]*3+2]);
    var e02 = vec3.fromValues(
      V[F[3*f+2]*3+0] - V[F[3*f+0]*3+0],
      V[F[3*f+2]*3+1] - V[F[3*f+0]*3+1],
      V[F[3*f+2]*3+2] - V[F[3*f+0]*3+2]);

    var n = vec3.create();
    vec3.cross(n,e01,e02);
    vec3.normalize(n,n);
    N[3*f+0] = n[0];
    N[3*f+1] = n[1];
    N[3*f+2] = n[2];
  }
  return N;
}
