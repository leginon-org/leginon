#include "em.h"
#include "mex.h"

char *getstr(const mxArray *mstr) {
  char *input_buf;
  size_t buflen;

  if(mxIsChar(mstr) != 1)
    mexErrMsgTxt("Input must be a string.");
  if(mxGetM(mstr) != 1)
    mexErrMsgTxt("Input must be a row vector.");
  buflen = (mxGetM(mstr) * mxGetN(mstr)) + 1;

  input_buf = mxMalloc(buflen*sizeof(char));

  if(mxGetString(mstr, input_buf, buflen) != 0)
    mexWarnMsgTxt("Not enough space. String is truncated.");

  return input_buf;
}

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) { 
 
  Py_Initialize();

  // Yikes...
  if(nrhs > 0) {
    char *uri = getstr(prhs[0]);
    if(nrhs > 1) {
      char *command = getstr(prhs[1]);
      if(strcmp(command, "get") == 0) {
        if(nrhs > 2) {
          char *key = getstr(prhs[2]);
          if(nlhs == 1) {
            if((strcmp(key, "magnification") == 0) ||
               (strcmp(key, "intensity") == 0) ||
               (strcmp(key, "screen current") == 0) ||
               (strcmp(key, "high tension") == 0) ||
               (strcmp(key, "spot size") == 0) ||
               (strcmp(key, "exposure time") == 0) ||
               (strcmp(key, "x offset") == 0) ||
               (strcmp(key, "y offset") == 0) ||
               (strcmp(key, "x dimension") == 0) ||
               (strcmp(key, "y dimension") == 0) ||
               (strcmp(key, "x binning") == 0) ||
               (strcmp(key, "y binning") == 0) ||
               (strcmp(key, "defocus") == 0)) {
              plhs[0] = mxCreateDoubleMatrix(1,1, mxREAL); 
              if(pobj2double(mxGetPr(plhs[0]),
                             addrgetitemfromstr(uri, key)) == -1)
                mexErrMsgTxt("Error getting value\n");
            } else if((strcmp(key, "image shift") == 0) ||
                      (strcmp(key, "gun tilt") == 0) ||
                      (strcmp(key, "gun shift") == 0) ||
                      (strcmp(key, "beam tilt") == 0) ||
                      (strcmp(key, "beam shift") == 0)) {
              plhs[0] = mxCreateDoubleMatrix(1,2, mxREAL); 
              if(pobj2vector(mxGetPr(plhs[0]), mxGetPr(plhs[0]) + 1,
                             addrgetitemfromstr(uri, key)) == -1)
                mexErrMsgTxt("Error getting value\n");
            } else if((strcmp(key, "stage position") == 0)) {
              plhs[0] = mxCreateDoubleMatrix(1,4, mxREAL); 
              if(pobj2stagevec(mxGetPr(plhs[0]), mxGetPr(plhs[0]) + 1,
                               mxGetPr(plhs[0]) + 2, mxGetPr(plhs[0]) + 3,
                               addrgetitemfromstr(uri, key)) == -1)
                mexErrMsgTxt("Error getting value\n");
            } else if((strcmp(key, "diffraction mode") == 0) ||
                      (strcmp(key, "low dose") == 0) ||
                      (strcmp(key, "low dose mode") == 0) ||
                      (strcmp(key, "exposure type") == 0) ||
                      (strcmp(key, "dark field mode") == 0)) {
              char *str;
              if(pobj2str(&str, addrgetitemfromstr(uri, key)) == -1)
                mexErrMsgTxt("Error getting value\n");
              plhs[0] = mxCreateString(str);
            } else if((strcmp(key, "image data") == 0)) {
              unsigned short *data;
              int size, dims[2];
              if(b64str2ushorts(&data, &size, addrgetitemfromstr(uri, key)) == -1)
                mexErrMsgTxt("Error getting value\n");
              if(pobj2int(&dims[0], addrgetitemfromstr(uri, "x dimension")) == -1)
                mexErrMsgTxt("Error getting value\n");
              if(pobj2int(&dims[1], addrgetitemfromstr(uri, "y dimension")) == -1)
                mexErrMsgTxt("Error getting value\n");
              plhs[0] = mxCreateNumericArray(2, dims, mxUINT16_CLASS, mxREAL);
              memcpy(mxGetPr(plhs[0]), data, size);
            } else
              mexErrMsgTxt("Invalid key parameter\n");
          } else
            mexErrMsgTxt("Invalid argument number, need one output argument\n");
          mxFree(key);
        } else
           mexErrMsgTxt("Invalid argument number, must specify key string\n"); 
      } else if(strcmp(command, "set") == 0) {
        if(nrhs > 3) {
          char *key = getstr(prhs[2]);
          if((strcmp(key, "magnification") == 0) ||
             (strcmp(key, "intensity") == 0) ||
             (strcmp(key, "screen current") == 0) ||
             (strcmp(key, "high tension") == 0) ||
             (strcmp(key, "spot size") == 0) ||
             (strcmp(key, "exposure time") == 0) ||
             (strcmp(key, "x offset") == 0) ||
             (strcmp(key, "y offset") == 0) ||
             (strcmp(key, "x dimension") == 0) ||
             (strcmp(key, "y dimension") == 0) ||
             (strcmp(key, "x binning") == 0) ||
             (strcmp(key, "y binning") == 0) ||
             (strcmp(key, "defocus") == 0)) {
            addrsetitemfromstr(uri, key, double2pobj(*mxGetPr(prhs[3])));
          } else if((strcmp(key, "image shift") == 0) ||
                    (strcmp(key, "gun tilt") == 0) ||
                    (strcmp(key, "gun shift") == 0) ||
                    (strcmp(key, "beam tilt") == 0) ||
                    (strcmp(key, "beam shift") == 0)) {
            addrsetitemfromstr(uri, key, vector2pobj(*mxGetPr(prhs[3]),
                                                     *(mxGetPr(prhs[3])+1)));
          } else if((strcmp(key, "stage position") == 0)) {
            double *vector = NULL;
            unsigned int m = 0, n = 0;

            m = mxGetM(prhs[3]);
            n = mxGetN(prhs[3]);
            if((m != 1) || (n != 4)) {
              mexErrMsgTxt(
                "stage position requires that input be a 1 x 4 vector.");
            }
            vector = mxGetPr(prhs[3]);
            addrsetitemfromstr(uri, key, stagevec2pobj(vector[0],
                                                       vector[1],
                                                       vector[2],
                                                       vector[3]));
          } else if((strcmp(key, "diffraction mode") == 0) ||
                    (strcmp(key, "low dose") == 0) ||
                    (strcmp(key, "low dose mode") == 0) ||
                    (strcmp(key, "exposure type") == 0) ||
                    (strcmp(key, "dark field mode") == 0)) {
            // leaks a bit
            addrsetitemfromstr(uri, key, str2pobj(getstr(prhs[3])));
          } else
            mexErrMsgTxt("Invalid key parameter\n");
        } else
           mexErrMsgTxt("Invalid argument number, must specify key string\n"); 
      } else
        mexErrMsgTxt("Invalid argument, must be get or set\n"); 
      mxFree(command);
    } else
      mexErrMsgTxt("Invalid argument number, must specify get or set\n"); 
    mxFree(uri);
   } else
      mexErrMsgTxt("Invalid argument number, must specify URI\n"); 
 
  Py_Finalize();
} 

