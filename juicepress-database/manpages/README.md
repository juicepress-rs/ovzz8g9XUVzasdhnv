# manpages

Manpages is a virtual source for the package guesser.

It uses the `ubuntu` sources to check whether a `library.so` or `executable` has a manpage entry. The result is binary (manpage exists \[+0\] or does not exist \[+1\]).

Given a `filename` in the firmware, the query is as follows:

```sql
SELECT location, file_name FROM ubuntu_file WHERE location ~* '^usr/share/man/' and file_name like 'filename.%':
```

Note that the filename is normalized: lowercase and in case of a versioned `.so.\d+.\d+`, we remove the version.
