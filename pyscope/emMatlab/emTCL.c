/*
 * COPYRIGHT:
 *       The Leginon software is Copyright 2003
 *       The Scripps Research Institute, La Jolla, CA
 *       For terms of the license agreement
 *       see  http://ami.scripps.edu/software/leginon-license
 */
#include <tcl.h>
#include "em.h"

int em(ClientData clientData, Tcl_Interp *interp, int objc, 
                                                char *objv[]) {
  Tcl_Obj *obj;

  Py_Initialize();

  if(objc > 1) {
    char *uri = objv[1];
    if(objc > 2) {
      char *command = objv[2];
      if(strcmp(command, "get") == 0) {
        if(objc > 3) {
          char *key = objv[3];
          if((strcmp(key, "exposure time") == 0) ||
             (strcmp(key, "spot size") == 0) ||
             (strcmp(key, "x offset") == 0) ||
             (strcmp(key, "y offset") == 0) ||
             (strcmp(key, "x dimension") == 0) ||
             (strcmp(key, "y dimension") == 0) ||
             (strcmp(key, "x binning") == 0) ||
             (strcmp(key, "y binning") == 0)) {
            int ival;
            if(pobj2int(&ival, addrgetitemfromstr(uri, key)) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            obj = Tcl_NewIntObj(ival);
            Tcl_SetObjResult(interp, obj);
          } else if((strcmp(key, "magnification") == 0) ||
             (strcmp(key, "intensity") == 0) ||
             (strcmp(key, "screen current") == 0) ||
             (strcmp(key, "high tension") == 0) ||
             (strcmp(key, "defocus") == 0)) {
            double dval;
            if(pobj2double(&dval, addrgetitemfromstr(uri, key)) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            obj = Tcl_NewDoubleObj(dval);
            Tcl_SetObjResult(interp, obj);
          } else if((strcmp(key, "image shift") == 0) ||
                    (strcmp(key, "gun tilt") == 0) ||
                    (strcmp(key, "gun shift") == 0) ||
                    (strcmp(key, "beam tilt") == 0) ||
                    (strcmp(key, "beam shift") == 0)) {
            double x, y;
            Tcl_Obj *objs[2];
            if(pobj2vector(&x, &y, addrgetitemfromstr(uri, key)) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            objs[0] = Tcl_NewDoubleObj(x);
            objs[1] = Tcl_NewDoubleObj(y);
            obj = Tcl_NewListObj(2, objs);
            Tcl_SetObjResult(interp, obj);
          } else if((strcmp(key, "stage position") == 0)) {
            double x, y, z, a;
            Tcl_Obj *objs[4];
            if(pobj2stagevec(&x,&y,&z,&a,addrgetitemfromstr(uri, key)) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            objs[0] = Tcl_NewDoubleObj(x);
            objs[1] = Tcl_NewDoubleObj(y);
            objs[2] = Tcl_NewDoubleObj(z);
            objs[3] = Tcl_NewDoubleObj(a);
            obj = Tcl_NewListObj(4, objs);
            Tcl_SetObjResult(interp, obj);
          } else if((strcmp(key, "diffraction mode") == 0) ||
                    (strcmp(key, "low dose") == 0) ||
                    (strcmp(key, "low dose mode") == 0) ||
                    (strcmp(key, "exposure type") == 0) ||
                    (strcmp(key, "dark field mode") == 0)) {
            char *str;
            if(pobj2str(&str, addrgetitemfromstr(uri, key)) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            obj = Tcl_NewStringObj(str, strlen(str));
            Tcl_SetObjResult(interp, obj);
          } else if((strcmp(key, "image data") == 0)) {
            char *ushortlist, *istr;
            unsigned short *i, *data;
            int size;

            b64str2ushorts(&data, &size,
                 addrgetitemfromstr(uri, "image data"));
            ushortlist = (char *)Tcl_Alloc((size/sizeof(unsigned short))
                                           *6*sizeof(char));
            istr = ushortlist;

            for(i = data; i < data + size/sizeof(unsigned short); i++) {
              sprintf(istr, "%hu ", *i);
              istr += strlen(istr);
            }

            obj = Tcl_NewStringObj(ushortlist, strlen(ushortlist));
            Tcl_SetObjResult(interp, obj);
            Tcl_Free(ushortlist);
          } else if((strcmp(key, "pixel size") == 0)) {
            PyObject *caldict;
            double pixsize, mag;
            char magstr[32];
            if(pobj2double(&mag,
                           addrgetitemfromstr(uri, "magnification")) == -1) {
              fprintf(stderr, "Error getting value\n");
              return TCL_ERROR;
            }
            snprintf(magstr, 32, "%f", mag);
            caldict = addrgetitemfromstr(uri, magstr);
            PyArg_Parse(PyDict_GetItemString(caldict, "pixel size"),
                        "d", &pixsize);
            obj = Tcl_NewDoubleObj(pixsize);
            Tcl_SetObjResult(interp, obj);
          } else {
            fprintf(stderr, "Invalid key parameter\n");
            return TCL_ERROR;
          }
        } else {
          fprintf(stderr, "Invalid argument number, must specify key string\n");
          return TCL_ERROR;
        }
      } else if(strcmp(command, "set") == 0) {
        if(objc > 4) {
          char *key = objv[3];
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
            addrsetitemfromstr(uri, key, double2pobj(atof(objv[4])));
          } else if((strcmp(key, "image shift") == 0) ||
                    (strcmp(key, "gun tilt") == 0) ||
                    (strcmp(key, "gun shift") == 0) ||
                    (strcmp(key, "beam tilt") == 0) ||
                    (strcmp(key, "beam shift") == 0)) {
            addrsetitemfromstr(uri, key, vector2pobj(atof(objv[4]),
                                                     atof(objv[5])));
          } else if((strcmp(key, "stage position") == 0)) {
            addrsetitemfromstr(uri, key, stagevec2pobj(atof(objv[4]),
                                                       atof(objv[5]),
                                                       atof(objv[6]),
                                                       atof(objv[7])));
          } else if((strcmp(key, "diffraction mode") == 0) ||
                    (strcmp(key, "low dose") == 0) ||
                    (strcmp(key, "low dose mode") == 0) ||
                    (strcmp(key, "exposure type") == 0) ||
                    (strcmp(key, "dark field mode") == 0)) {
            addrsetitemfromstr(uri, key, str2pobj(objv[4]));
          } else {
            fprintf(stderr, "Invalid key parameter\n");
            return TCL_ERROR;
          }
        } else {
          fprintf(stderr, "Invalid argument number, must specify key string\n");
          return TCL_ERROR;
        }
      } else if((strcmp(command, "autofocus") == 0) ||
                (strcmp(command, "normalizeLens") == 0) ||
                (strcmp(command, "resetDefocus") == 0)) {
        PyObject *client, *args;
        client = newclient(uri);
        args = PyTuple_New(0);
        callmethod(client, command, args);
        Py_DECREF(args);
        delclient(client);
      } else if(strcmp(command, "imageshift") == 0) {
        if(objc > 4) {
          PyObject *client, *args;
          client = newclient(uri);
          args = PyTuple_New(3);
          PyTuple_SetItem(args, 0, int2pobj(atoi(objv[3])));
          PyTuple_SetItem(args, 1, int2pobj(atoi(objv[4])));
          PyTuple_SetItem(args, 2, str2pobj("relative"));
          callmethod(client, command, args);
          Py_DECREF(args);
          delclient(client);
        }
      } else {
        fprintf(stderr, "Invalid argument for command\n");
        return TCL_ERROR;
      }
    } else {
      fprintf(stderr, "Invalid argument number, must specify get or set\n");
      return TCL_ERROR;
    }
  } else {
     fprintf(stderr, "Invalid argument number, must specify URI\n");
     return TCL_ERROR;
  }

  Py_Finalize();

  return TCL_OK;
}

int Emtcl_Init(Tcl_Interp* interp) {
  int status;

  status = Tcl_Init(interp);

  if(status != TCL_OK)
    return TCL_ERROR;

  Tcl_CreateCommand(interp, "em", em, NULL, NULL);

  return TCL_OK;
}

