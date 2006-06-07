
#include "string.h"
#include "time.h"
#include "stdio.h"
#include "errno.h"

/**
 * _logger(char *filename, char* data)
 * 
 * print current function information
 *
 */
void _logger(char *filename, char* data) {
	FILE *fp;
	time_t tm;
	struct tm *ptr;
	char str_t[100];
	if ((fp=fopen(filename , "a")) != NULL) {
		tm = time(NULL);
		ptr = localtime(&tm);
		strftime(str_t, 100, "%c",ptr);
/*
		fprintf( fp, "[%s]: file: %s - function: %s - param %s \n", 
				str_t,
				zend_get_executed_filename(TSRMLS_C),
			get_active_function_name(TSRMLS_C),
				data);
*/
		fprintf( fp, "[%s]: %s \n", 
				str_t,
				data);
		fclose(fp);
	}
}

/*
 Example:

	char data[1024];
	sprintf(data, "im->sx %i : im->sy %i", im->sx, im->sy);
	_logger("/tmp/php_mrc.log", data);
*/
