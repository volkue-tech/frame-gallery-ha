#include <stdio.h>
#include "posixtz.h"

int usage() {
	printf("Print POSIX TZ string from compiled tzdata\n"
		"Usage: posixtz FILE...\n");
	return -1;
}

int main(int argc, char *argv[])
{
	int i=1;
	if (argc <= 1)
		return usage();

	for (i = 1; i < argc; i++) {
		char *s = posix_tz(argv[i++]);
		if (s != NULL)
			printf("%s\n", s);
	}
	return 0;
}

