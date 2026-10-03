/* ripped from uclibc 
*
* Copyright (C) 2010 Denys Vlasenko <vda.linux@googlemail.com>
* Copyright (C) 2011 Natanael Copa <ncopa@alpinelinux.org>
*
* GNU Library General Public License (LGPL) version 2 or later.
*
*/

#include <sys/stat.h>
#include <sys/types.h>

#include <err.h>
#include <fcntl.h>
#include <limits.h>
#include <stdio.h>

#include "posixtz.h"

#ifndef TZNAME_MAX
#define TZNAME_MAX _POSIX_TZNAME_MAX
#endif

#define TZ_BUFLEN               (2*TZNAME_MAX + 56)

char *posix_tz(const char *filename)
{
	int fd, r;
	static char buf[TZ_BUFLEN];
	char *p = NULL;
	fd = open(filename, O_RDONLY);
	if (fd < 0)
		return NULL;
	
	r = read(fd, buf, TZ_BUFLEN);
	if (r != TZ_BUFLEN
	    || strncmp(buf, "TZif", 4) != 0
	    || (unsigned char)buf[4] < 2
	    || lseek(fd, -TZ_BUFLEN, SEEK_END) < 0
	   )
		goto ERROR;

	/* tzfile.h from tzcode database says about TZif2+ files:
	**
	** If tzh_version is '2' or greater, the above is followed by a second instance
	** of tzhead and a second instance of the data in which each coded transition
	** time uses 8 rather than 4 chars,
	** then a POSIX-TZ-environment-variable-style string for use in handling
	** instants after the last transition time stored in the file
	** (with nothing between the newlines if there is no POSIX representation for
	** such instants).
	*/
	r = read(fd, buf, TZ_BUFLEN);
	if (r <= 0 || buf[--r] != '\n')
		goto ERROR;
	buf[r] = 0;
	while (r != 0) {
		if (buf[--r] == '\n') {
			p = buf + r + 1;
			break;
		}
	} /* else ('\n' not found): p remains NULL */
ERROR:
	close(fd);
	return p;
}

