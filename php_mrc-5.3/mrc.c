#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mrc.h"

/* {{{ static void byteswap2(unsigned char *pbyData) */
static void byteswap2(unsigned char *pbyData) {
	unsigned char byTemp;
	byTemp  = pbyData[0];
	pbyData[0] = pbyData[1];
	pbyData[1] = byTemp;
}
/* }}} */

/* {{{ static void byteswap4(unsigned char *pbyData) */
static void byteswap4(unsigned char *pbyData) {
	unsigned char byTemp0;
	unsigned char byTemp1;

	byTemp0  = pbyData[0];
	byTemp1  = pbyData[1];
	pbyData[0] = pbyData[3];
	pbyData[1] = pbyData[2];
	pbyData[2] = byTemp1;
	pbyData[3] = byTemp0;
}
/* }}} */

/* {{{ void byteswapbuffer(void *pData, unsigned int uElements, unsigned int uElementSize) */
void byteswapbuffer(void *pData, unsigned int uElements, unsigned int uElementSize) {

	unsigned char *pbyData = (unsigned char *)pData;
	unsigned int cuElements = uElements;

	while(cuElements > 0) {
		if(uElementSize == 2)
			byteswap2(pbyData);
		else if(uElementSize == 4)
			byteswap4(pbyData);
		else
			return;
		pbyData += uElementSize;
		cuElements--;
	}
}
/* }}} */

/* {{{ int byteswapread(FILE *pFRead, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) */
int byteswapread(FILE *pFRead, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) {

 	unsigned int uResult = 0;
    uResult = fread((char *)pBuffer, uElementSize, uElements, pFRead);
	if(ferror(pFRead)) {
		return -1;
	}
	
	if(((fuByteOrder == LITTLE_ENDIAN_DATA) && BIG_ENDIAN_HOST) ||
		((fuByteOrder == BIG_ENDIAN_DATA) && LITTLE_ENDIAN_HOST))
		byteswapbuffer(pBuffer, uElements, uElementSize);
    return uResult;
}
/* }}} */

/* {{{ int byteswapwrite(FILE *pFWrite, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) */
int byteswapwrite(FILE *pFWrite, void *pBuffer, unsigned int uElements,
				 unsigned int uElementSize, unsigned int fuByteOrder) {

 	unsigned int uResult = 0;
	if(((fuByteOrder == LITTLE_ENDIAN_DATA) && BIG_ENDIAN_HOST) ||
		((fuByteOrder == BIG_ENDIAN_DATA) && LITTLE_ENDIAN_HOST))
		byteswapbuffer(pBuffer, uElements, uElementSize);

		uResult = fwrite((char *)pBuffer, uElementSize, uElements, pFWrite);

	if(ferror(pFWrite)) {
		return -1;
	}
	
    return uResult;
}
/* }}} */


/* {{{ int readMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader)  */
int readMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader) {
		unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

    byteswapread(pFMRC, &pMRCHeader->nx, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->ny, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nz, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mode, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nxstart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nystart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nzstart, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mx, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->my, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mz, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->x_length, 1, 4, fuByteOrder); 
    byteswapread(pFMRC, &pMRCHeader->y_length, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->z_length, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->alpha, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->beta, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->gamma, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mapc, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->mapr, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->maps, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amax, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->amean, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->ispg, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nsymbt, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->extra, 4*MRC_USER, 1, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->xorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->yorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->zorigin, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->map, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->machstamp, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->rms, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->nlabl, 1, 4, fuByteOrder);
    byteswapread(pFMRC, &pMRCHeader->label, MRC_LABEL_SIZE*MRC_NUM_LABELS, 1, fuByteOrder);
	
    if((pMRCHeader->nx < 0) || (pMRCHeader->ny < 0) || (pMRCHeader->nz < 0) ||
		(pMRCHeader->mode < 0) || (pMRCHeader->mode > 4))
        return -1; /* This is not a valid pMRCHeader header */

	return 1 ;
}
/* }}} */

/* {{{ int loadMRCHeader(char *pszFilename, MRCHeader *pMRCHeader) */
int loadMRCHeader(char *pszFilename, MRCHeader *pMRCHeader) {
	FILE *pFMRC;


	if((pFMRC = fopen(pszFilename, "rb")) == NULL)
		return -1;


	if(!readMRCHeader(pFMRC, pMRCHeader)) {
		fclose(pFMRC);
		return -1;
	}

	fclose(pFMRC);
	return 1;
}
/* }}} */

/* {{{ int loadMRC(char *pszFilename, MRC *pMRC) */
int loadMRC(char *pszFilename, MRC *pMRC) {
	FILE *pFMRC;
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;
	unsigned int maxElement=500000000;

	if((pFMRC = fopen(pszFilename, "rb")) == NULL)
		return -1;

	if(!readMRCHeader(pFMRC, &(pMRC->header)))
		return -1;

	uElements = pMRC->header.nx * pMRC->header.ny * pMRC->header.nz;

	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_UNSIGNED_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}

    if((pMRC->pbyData = malloc(uElements*uElementSize)) == NULL)
    	pMRC->pbyData = malloc(uElements*uElementSize);

	if (uElements>maxElement) {
		/*  --- split writing in two ---  */
		if(byteswapread(pFMRC, &(pMRC->pbyData[0]), uElements-maxElement, uElementSize, fuByteOrder) == -1) {
			free(pMRC->pbyData);
			fclose(pFMRC);
			return -1;
		}
		if(byteswapread(pFMRC, &(pMRC->pbyData[uElements-maxElement]), maxElement, uElementSize, fuByteOrder) == -1) {
			free(pMRC->pbyData);
			fclose(pFMRC);
			return -1;
		}
	} else {
		if(byteswapread(pFMRC, pMRC->pbyData, uElements, uElementSize, fuByteOrder) == -1) {
			free(pMRC->pbyData);
			fclose(pFMRC);
			return -1;
		}
	}
	
	fclose(pFMRC);
  return 1;
}
/* }}} */

/* {{{ int writeMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader) */
int writeMRCHeader(FILE *pFMRC, MRCHeader *pMRCHeader) {
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;

	byteswapwrite(pFMRC, &pMRCHeader->nx, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->ny, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nz, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mode, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nxstart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nystart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nzstart, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mx, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->my, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mz, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->x_length, 1, 4, fuByteOrder); 
	byteswapwrite(pFMRC, &pMRCHeader->y_length, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->z_length, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->alpha, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->beta, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->gamma, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mapc, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->mapr, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->maps, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amax, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->amean, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->ispg, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nsymbt, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->extra, 4*MRC_USER, 1, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->xorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->yorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->zorigin, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->map, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->machstamp, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->rms, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->nlabl, 1, 4, fuByteOrder);
	byteswapwrite(pFMRC, &pMRCHeader->label, MRC_LABEL_SIZE*MRC_NUM_LABELS, 1, fuByteOrder);
	
	return 1 ;
}
/* }}} */

/* {{{ int writeMRC(FILE *pFMRC, MRC *pMRC) */
int writeMRC(FILE *pFMRC, MRC *pMRC) {
	unsigned int uElementSize = 0;
	unsigned int uElements = 0;
	unsigned int fuByteOrder = LITTLE_ENDIAN_DATA;
	unsigned int maxElement=500000000;

	uElements = pMRC->header.nx * pMRC->header.ny; /*   * pMRC->header.nz; */
	switch(pMRC->header.mode) {
		case MRC_MODE_BYTE:
			uElementSize = sizeof(char);
			break;
		case MRC_MODE_SHORT:
			uElementSize = sizeof(short);
			break;
		case MRC_MODE_FLOAT:
			uElementSize = sizeof(float);
			break;
		case MRC_MODE_SHORT_COMPLEX:
			uElementSize = sizeof(short);
			uElements *= 2;
			break;
		case MRC_MODE_FLOAT_COMPLEX:
			uElementSize = sizeof(float);
			uElements *= 2;
			break;
		default:
			return -1;
	}

	if(!writeMRCHeader(pFMRC, &(pMRC->header)))
		return -1;

	if (uElements>maxElement) {
		/*  --- split writing in two ---  */
		if(byteswapwrite(pFMRC, &(pMRC->pbyData[0]), uElements-maxElement, uElementSize, fuByteOrder) == -1)
			return -1;
		if(byteswapwrite(pFMRC, &(pMRC->pbyData[uElements-maxElement]), maxElement, uElementSize, fuByteOrder) == -1)
			return -1;
	} else {
		if(byteswapwrite(pFMRC, pMRC->pbyData, uElements, uElementSize, fuByteOrder) == -1)
			return -1;
	}

		return 1;
}
/* }}} */


/* {{{ int readImagic5Header(FILE *pFHeader, Imagic5Header *pHeader, int img_num) */
int readImagic5Header(FILE *pFHeader, Imagic5Header *pHeader, int img_num) {
	unsigned int uResult;
	if (img_num!=0) {
		fseek(pFHeader, img_num*SIZEOF_I5_HEADER, SEEK_CUR);
	}
	uResult = fread((void *)pHeader, 1, SIZEOF_I5_HEADER, pFHeader);
	if(ferror(pFHeader) || (uResult != SIZEOF_I5_HEADER))
		return -1;
	return 1;
}
/* }}} */

/* {{{ int readImagic5(FILE *hedstream, FILE *imgstream, Imagic5 *pImagic5) */
int readImagic5(FILE *hedstream, FILE *imgstream, Imagic5 *pImagic5) {

	int nResult = -1;
	void *pResult = NULL;
	unsigned int cui = 0;
	Imagic5Header header;

	nResult = (int)readImagic5Header(hedstream, &header, 0);
	if(!nResult)
		return -1;

	pImagic5->uCount = header.count+1;
	if(pImagic5->uCount <= 0)
		return -1;

	pImagic5->pHeaders = (Imagic5Header *)malloc(pImagic5->uCount*SIZEOF_I5_HEADER);
	if(pImagic5->pHeaders == NULL)
		return -1;

	memcpy(&(pImagic5->pHeaders[0]), &header, SIZEOF_I5_HEADER);

	for(cui = 1; cui < pImagic5->uCount; cui++) {
		nResult = readImagic5Header(hedstream, &(pImagic5->pHeaders[cui]), 0);
		if(!nResult) {
			freeImagic5(pImagic5);
			return -1;
		}
	}

	pResult = readImagic5Images(imgstream, pImagic5);
	if(pResult == NULL) {
		freeImagic5(pImagic5);
		return -1;
	}
	
	pImagic5->pbyData = pResult;

	return 1;
}
/* }}} */

/* {{{ int readImagic5At(FILE *hedstream, FILE *imgstream, int img_num, Imagic5one *pImagic5) */
int readImagic5At(FILE *hedstream, FILE *imgstream, int img_num, Imagic5one *pImagic5) {

	int nResult = -1;
	void *pResult = NULL;
	unsigned int cui = 0;
	Imagic5Header header;

		
	nResult = readImagic5Header(hedstream, &header, 0);
	memcpy(&(pImagic5->header), &header, SIZEOF_I5_HEADER);

	if(!nResult)
		return -1;

	nResult = readImagic5Header(hedstream, &(pImagic5->header), img_num);

	pResult = readImagic5ImagesAt(imgstream, img_num, pImagic5);
	if(pResult == NULL) {
		freeImagic5one(pImagic5);
		return -1;
	}
	
	pImagic5->pbyData = pResult;

}
/* }}} */


/* {{{ int loadImagic5Header(char *pszFilename, Imagic5Header *pHeader, int img_num) */
int loadImagic5Header(char *pszFilename, Imagic5Header *pHeader, int img_num) {
	FILE *pF;

	if((pF = fopen(pszFilename, "rb")) == NULL)
		return -1;

	if(!readImagic5Header(pF, pHeader, img_num)) {
		fclose(pF);
		return -1;
	}

	fclose(pF);
	return 1;
}
/* }}} */

/* {{{ int loadImagic5(char *pszName, Imagic5 *pImagic5) */
int loadImagic5(char *pszName, Imagic5 *pImagic5) {
	char *pszFilename = NULL;
	FILE *pFHED = NULL;
	FILE *pFIMG = NULL;

	pszFilename = (char *)malloc(strlen(pszName) + 5);
	if(pszFilename == NULL)
		return -1;

	sprintf(pszFilename, "%s.hed", pszName);
    if((pFHED = fopen(pszFilename, "rb")) == NULL) {
		return -1;
	}

	sprintf(pszFilename, "%s.img", pszName);
    if((pFIMG = fopen(pszFilename, "rb")) == NULL) {
		fclose(pFHED);
		return -1;
	}
	free(pszFilename);


	if(!readImagic5(pFHED, pFIMG, pImagic5)) {
		fclose(pFHED);
		fclose(pFIMG);
		return -1;
	}

	fclose(pFHED);
	fclose(pFIMG);
    
    return 1;
}
/* }}} */

/* {{{ int loadImagic5At(char *pszHedName, char *pszImgName, int img_num, Imagic5one *pImagic5) */
int loadImagic5At(char *pszHedName, char *pszImgName, int img_num, Imagic5one *pImagic5) {
	FILE *pFHED;
	FILE *pFIMG;

	if((pFHED = fopen(pszHedName, "rb")) == NULL) {
		return -1;
	}

	if((pFIMG = fopen(pszImgName, "rb")) == NULL) {
		fclose(pFHED);
		return -1;
	}

	if(!readImagic5At(pFHED, pFIMG, img_num, pImagic5)) {
		fclose(pFHED);
		fclose(pFIMG);
		return -1;
	}

	fclose(pFHED);
	fclose(pFIMG);
    
	return 1;
}
/* }}} */


/* {{{ void *readImagic5Images(FILE *pFImage, Imagic5 *pImagic5) */
void *readImagic5Images(FILE *pFImage, Imagic5 *pImagic5) {
	void *pData = NULL;
	size_t size = 0;
	unsigned int uResult = 0;
	char *psType = pImagic5->pHeaders[0].type;
	unsigned int uElements = pImagic5->pHeaders[0].pixels;
	
	if(strcmp(psType, "REAL") == 0)
		size = sizeof(float);
	else if(strcmp(psType, "INTG") == 0)
		size = sizeof(short);
	else if(strcmp(psType, "PACK") == 0)
		size = sizeof(char);
	else if(strcmp(psType, "COMP") == 0)
		size = 2*sizeof(float);
	pData = malloc(size * uElements * pImagic5->uCount);
	if(pData == NULL)
		return NULL;

	uResult = fread(pData, 1, size*uElements*pImagic5->uCount, pFImage);
	if(ferror(pFImage)) {
		free(pData);
		return NULL;
	}
/*
	if(!byteswapread(pFImage, pData, size, uElements*pImagic5->uCount, BIG_ENDIAN_DATA)) {
		free(pData);
		return NULL;
	}
*/
	return pData;
}
/* }}} */

/* {{{ void *readImagic5ImagesAt(FILE *pFImage, int img_num, Imagic5one *pImagic5) */
void *readImagic5ImagesAt(FILE *pFImage, int img_num, Imagic5one *pImagic5) {
	void *pData = NULL;
	size_t size = 0;
	unsigned int uResult = 0;
	char *psType = pImagic5->header.type;
	unsigned int uElements = pImagic5->header.pixels;
	
	if(strcmp(psType, "REAL") == 0)
		size = sizeof(float);
	else if(strcmp(psType, "INTG") == 0)
		size = sizeof(short);
	else if(strcmp(psType, "PACK") == 0)
		size = sizeof(char);
	else if(strcmp(psType, "COMP") == 0)
		size = 2*sizeof(float);
	pData = malloc(size * uElements );
	if(pData == NULL)
		return NULL;

	/*  --- position pointer file where copy should start: (srcX, srcY); */
	if (img_num!=0) {
		fseek(pFImage, img_num*size*uElements, SEEK_CUR);
	}

	uResult = fread(pData, 1, size*uElements, pFImage);
	if(ferror(pFImage)) {
		free(pData);
		return NULL;
	}
	if(!byteswapread(pFImage, pData, size, 1, BIG_ENDIAN_DATA)) {
		free(pData);
		return NULL;
	}
	return pData;
}
/* }}} */

/* {{{ void freeImagic5(Imagic5 *pImagic5) */
void freeImagic5(Imagic5 *pImagic5) {

	unsigned int cuImage = 0;

	if(pImagic5->pHeaders != NULL) {
		free(pImagic5->pHeaders);
		pImagic5->pHeaders = NULL;
	}

	if(pImagic5->pbyData != NULL) {
		free(pImagic5->pbyData);
		pImagic5->pbyData = NULL;
	}

	pImagic5->uCount = -1;
}
/* }}} */

/* {{{ void freeImagic5one(Imagic5one *pImagic5) */
void freeImagic5one(Imagic5one *pImagic5) {

	if(pImagic5->pbyData != NULL) {
		free(pImagic5->pbyData);
		pImagic5->pbyData = NULL;
	}

}
/* }}} */


/* {{{ vim command
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * End:
 * vim600: noet sw=4 ts=4 fdm=marker
 * vim<600: noet sw=4 ts=4
 }}} */
