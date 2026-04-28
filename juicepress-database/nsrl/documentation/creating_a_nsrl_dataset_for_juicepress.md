
### 1. Get RDS the modern dataset 

```bash
$ wget https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2025.03.1/RDS_2025.03.1_modern_minimal.zip
$ unzip RDS_2025.03.1_modern_minimal.zip # takes a lot of time, roughly 178gb of data
$ tree RDS_2025.03.1_modern_minimal

RDS_2025.03.1_modern_minimal
├── RDS_2025.03.1_modern_minimal.db
├── RDS_2025.03.1_modern_minimal.schema.sql
├── readme.txt
└── signatures.txt

1 directory, 4 files

```

### 2. bulk export relevant tables from sqlite to csv

Goal: create csv files that can be bulk-imported into psql

```cardlink
url: https://www.sqlitetutorial.net/sqlite-export-csv/
title: "Export SQLite Database To a CSV File"
description: "This tutorial shows you how to export data in the SQLite database to a CSV file using sqlite3 and SQLite Studio tools."
host: www.sqlitetutorial.net
favicon: https://www.sqlitetutorial.net/wp-content/uploads/2016/05/favicon-150x150.png
image: https://www.sqlitetutorial.net/wp-content/uploads/2016/05/SQLite-Export-CSV-example.png
```


**WARNING: DO THE SAME WITH LEGACY PACKAGES**

#### 2.1. FILE (file information associated with software packages)

this writes all 410,281,065 rows of the FILE table to disk (17GiB)

```shell
sqlite3 RDS_2025.03.1_modern_minimal/RDS_2025.03.1_modern_minimal.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output file.csv
sqlite> select file_name,file_size,package_id from FILE;
# takes time to write , drops file hashes and crc
```


#### 2.2. PKG (software packages)

***WARNING: SOFTWARE PACKAGE IDS ARE NOT UNIQ!!!***

139,483 software packages

```shell
sqlite3 RDS_2025.03.1_modern_minimal/RDS_2025.03.1_modern_minimal.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output pkg.csv
sqlite> select package_id,name,operating_system_id,manufacturer_id from PKG;
```

#### 2.4. OS (operating systems)

331 os entries

```shell
sqlite3 RDS_2025.03.1_modern_minimal/RDS_2025.03.1_modern_minimal.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output os.csv
sqlite> select operating_system_id,name,manufacturer_id from OS;
```

#### 2.4 MFG (manufacturer)

2,351 MFG records


```shell
sqlite3 RDS_2025.03.1_modern_minimal/RDS_2025.03.1_modern_minimal.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output mfg.csv
sqlite> select * from MFG;
```


### 3. create psql server:

after this, postgres v 17.4 listens on `localhost:5432` with login `postgres:postgres`

```yaml
services:
  db:
    image: postgres:17.4-alpine3.21
    shm_size: 128mb
    environment:
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./raw_sql:/raw_sql
    ports:
      - 127.0.0.1:5432:5432

volumes:
  pgdata:
```

```shell
docker compose up -d
```

### 4. seed data

#### 4.1. prepare database



```shell
docker exec -it nsrl-db-1 /bin/ash
psql -U postgres
```

```sql
CREATE DATABASE nsrl;
```

#### 4.2. prepare tables

script here [[nsrl_create.sql]]


```shell
docker exec -it nsrl-db-1 /bin/ash
psql -U postgres nsrl
```

##### 4.2.1. file

```sql
CREATE TABLE file (
    file_name varchar NOT NULL,
    file_size bigint NOT NULL,
    package_id bigint NULL
);
```


##### 4.2.2. pkg

```sql
CREATE TABLE pkg (
    package_id bigint NOT NULL,
    name varchar NOT NULL,
    operating_system_id bigint NULL,
    manufacturer_id bigint NULL
);
```

##### 4.2.3. os

```sql
CREATE TABLE os (
    operating_system_id bigint PRIMARY KEY NOT NULL,
    name varchar NOT NULL,
    manufacturer_id bigint NULL
);
```

##### 4.2.4. mfg

```sql
CREATE TABLE mfg (
    manufacturer_id bigint PRIMARY KEY NOT NULL,
    name varchar NOT NULL
);
```


#### 4.3. import all tables

```cardlink
url: https://infinum.com/blog/superfast-csv-imports-using-postgresqls-copy/
title: "Superfast CSV Imports Using PostgreSQL's COPY Command"
description: "Dealing with various sources of data in web applications requires us to create services that will extract information from CSV, Excel, and other file types."
host: infinum.com
favicon: https://infinum.com/wp-content/themes/redesign/public/favicon.png
image: https://wp-assets.infinum.com/uploads/2017/09/superfast-csv-imports-using-postgresqls-copy-0.png
```


**Put the created csv files into `./raw_sql` relative to `docker-compose.yml`, then:**

```sql
COPY file FROM '/raw_sql/file.csv' CSV HEADER;
COPY file FROM '/raw_sql/file_legacy.csv' CSV HEADER;
COPY pkg FROM '/raw_sql/pkg_legacy.csv' CSV HEADER;
COPY pkg FROM '/raw_sql/pkg.csv' CSV HEADER;
COPY mfg FROM '/raw_sql/mfg.csv' CSV HEADER;
COPY mfg FROM '/raw_sql/mfg_legacy.csv' CSV HEADER;
COPY os FROM '/raw_sql/os.csv' CSV HEADER;
COPY os FROM '/raw_sql/os_legacy.csv' CSV HEADER;
```

### 6. Tune Lookups: create file_name index on `file` table

#### 6.1. trimming the database

**We discard all file names that are _not_ in packages that are from Linux- and BSD-based OSs**

List of discarded OS ids: [[discarded_nsrl_oses.csv]]
SQL: [[nsrl_speedup.sql]]

```sql
delete from os where operating_system_id in (1,
4,
20,
23,
28,
31,
32,
33,
34,
35,
36,
37,
38,
42,
43,
44,
45,
50,
56,
57,
58,
59,
61,
62,
63,
64,
65,
66,
67,
68,
69,
71,
76,
77,
78,
79,
83,
84,
86,
92,
93,
96,
100,
101,
104,
110,
112,
120,
121,
122,
126,
127,
128,
139,
141,
143,
144,
145,
146,
147,
148,
149,
150,
151,
152,
154,
156,
157,
159,
160,
164,
165,
166,
169,
170,
171,
174,
176,
180,
186,
189,
190,
191,
192,
194,
195,
196,
197,
198,
199,
200,
204,
205,
206,
207,
208,
209,
210,
211,
212,
213,
214,
215,
216,
217,
218,
219,
220,
221,
222,
223,
224,
226,
227,
228,
229,
230,
231,
232,
233,
234,
237,
238,
239,
240,
241,
244,
245,
247,
248,
249,
250,
251,
252,
253,
254,
256,
257,
258,
259,
260,
261,
262,
263,
264,
265,
267,
268,
269,
270,
271,
272,
273,
274,
277,
278,
279,
280,
281,
282,
283,
284,
285,
286,
288,
290,
291,
292,
297,
298,
299,
300,
302,
306,
307,
308,
309,
310,
311,
313,
314,
315,
320,
323,
324,
325,
326,
327,
328,
330,
331,
332,
333,
335,
337,
339,
340,
345,
346,
347,
348,
349,
352,
353,
354,
357,
358,
359,
363,
364,
365,
366,
368,
369,
370,
371,
377,
378,
379,
385,
386,
387,
388,
389,
390,
391,
392,
393,
394,
395,
396,
397,
398,
399,
400,
401,
403,
404,
407,
409,
410,
413,
414,
415,
416,
417,
419,
421,
423,
424,
425,
433,
437,
438,
441,
442,
443,
448,
449,
453,
461,
462,
464,
465,
466,
467,
469,
471,
472,
480,
481,
482,
483,
487,
488,
489,
490,
491,
492,
493,
494,
497,
498,
502,
513,
514,
515,
525,
527,
528,
529,
531,
534,
535,
543,
544,
550,
551,
552,
553,
559,
561,
562,
563,
564,
565,
569,
571,
575,
576,
577,
578,
579,
580,
581,
584,
585,
586,
590,
593,
602,
609,
610,
613,
614,
615,
616,
617,
618,
619,
621,
622,
639,
642,
658,
660,
661,
662,
666,
671,
672,
683,
684,
688,
689,
694,
695,
696,
697,
698,
700,
707,
716,
718,
720,
724,
726,
727,
728,
729,
731,
732,
737,
738,
739,
748,
749,
761,
762,
763,
764,
765,
766,
768,
771,
772,
775,
779,
783,
785,
786,
787,
788,
789,
790,
804,
805,
809,
815,
817,
819,
822,
823,
824,
827,
859,
867,
868,
869,
879,
880,
882,
884,
885,
892,
893,
894,
895,
896,
897,
898,
900,
901,
902,
903,
904,
905,
906,
907,
919,
920,
922,
974,
976,
977,
978,
979,
980,
981,
983,
1002,
1014,
1018,
1019,
1021,
1022,
1028,
1029,
1030,
1031,
1033,
1038,
1039,
1049,
1053,
1069,
1072,
1073,
1075,
1076,
1077,
1112,
1138,
1141,
1144,
1148,
1156,
1159,
1176,
1177,
1178,
1193,
1199,
1202,
1210,
1311,
1318,
1357,
1358,
1359,
1365,
1366,
1403,
1404,
1406,
1407,
1408,
1409,
1415,
1416,
1417,
1419,
1444,
1445,
1446,
1448,
1450,
1451,
1452,
1453,
1454,
1455,
1460,
1461,
1462,
1464,
1465,
1466,
1467,
1468,
1667,
1701,
1702,
1766,
1898,
1899,
1931,
1964,
2261,
2262,
2263,
2294,
2789,
2790,
2888);

/* remove os dupes */
alter table os add column tmp_key bigint generated always as identity;
delete from os where tmp_key in (with part as (select tmp_key,row_number() over (partition by operating_system_id) from os) select tmp_key from part where row_number>=2);
alter table os drop column tmp_key;
alter table os add constraint pk_operating_system_id primary key (operating_system_id);

/* remove non-linux pkgs */
delete from pkg where operating_system_id not in (select operating_system_id from os);

/* remove dupes for pkgs*/*
alter table pkg add column tmp_key bigint generated always as identity;
delete from pkg where tmp_key in (with part as (select tmp_key,row_number() over (partition by package_id) from pkg) select tmp_key from part where row_number>=2);
alter table pkg drop column tmp_key;
alter table pkg add constraint pk_package_id primary key (package_id);

/* prune non-linux manufacturers */
delete from mfg where manufacturer_id not in (select manufacturer_id from os) and manufacturer_id not in (select manufacturer_id from pkg);

/* remove dupes from mfgs */
alter table mfg add column tmp_key bigint generated always as identity;
delete from mfg where tmp_key in (with part as (select tmp_key,row_number() over (partition by manufacturer_id) from mfg) select tmp_key from part where row_number>=2);
alter table mfg drop column tmp_key;
alter table mfg add constraint pk_manufacturer_id primary key (manufacturer_id);

/* prune non-linux files */
/* LOL this killed 413,717,787 files! */
delete from file where package_id not in (select package_id from pkg);


/* 158,969,730 filenames left*/
select count(1) from file;
```

#### 6.2 create btree index of file_name for fast `=` queries

Takes 7+ minutes. **Note that this does not accelerate LIKE AND ILIKE QUERIES, ESPECIALLY THE ONES THAT START WITH A WILDCARD (`%`)**

```sql
ALTER TABLE file ADD COLUMN file_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY;
CREATE INDEX file_name_idx ON file USING btree (file_name);
```

#### 6.3. create gin index for trigrams in `file` to make `LIKE` and `ILIKE` queries ridiculously fast

[[nsrl_gin_trigram.sql]]

```cardlink
url: https://www.cybertec-postgresql.com/en/postgresql-more-performance-for-like-and-ilike-statements/
title: "PostgreSQL: More performance for LIKE and ILIKE statements"
description: "This blogpost shows what PostgreSQL can do to speed up LIKE and ILIKE to archieve better PostgreSQL database performance."
host: www.cybertec-postgresql.com
favicon: https://www.cybertec-postgresql.com/favicon-32x32.png
image: https://www.cybertec-postgresql.com/wp-content/uploads/2020/07/PostgreSQL-More-Performance-for-LIKE-and-ILIKE-statements-Hans-Jurgen-Schonig.png
```


```cardlink
url: https://www.postgresql.org/docs/current/gin.html
title: "64.4. GIN Indexes"
description: "64.4.&nbsp;GIN Indexes # 64.4.1. Introduction 64.4.2. Built-in Operator Classes 64.4.3. Extensibility 64.4.4. Implementation 64.4.5. GIN Tips and Tricks 64.4.6. Limitations …"
host: www.postgresql.org
image: https://www.postgresql.org/media/img/about/press/elephant.png
```


```sql
/* postgres trigram extension */
create extension pg_trgm;

/* took 1m 34s */
create index file_name_gin_idx on file using gin (file_name gin_trgm_ops);
  
/* this went down from over 4min to 0.080s */
select * from file where file_name ilike 'cli%' and SIMILARITY(file_name, 'cli') > 0.9;
```

#### 6.4. boost `package_id` lookups on `file` with a btree idx

```sql
create index file_pkg_idx on file using btree (package_id);
```
