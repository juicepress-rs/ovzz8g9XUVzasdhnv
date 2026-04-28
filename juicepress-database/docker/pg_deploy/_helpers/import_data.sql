/* Trigram extension from postgresql-contrib for GIN indices*/

CREATE EXTENSION pg_trgm;

/* BUILDROOT */

CREATE TABLE buildroot_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT buildroot_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE buildroot_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT buildroot_file_pk PRIMARY KEY (id)
);

COPY buildroot_pkg FROM '/tmp/pg_deploy/tables/buildroot/buildroot_pkg.csv' CSV HEADER;
COPY buildroot_file FROM '/tmp/pg_deploy/tables/buildroot/buildroot_file.csv' CSV HEADER;

CREATE INDEX buildroot_file_name_gin_idx ON buildroot_file USING gin (file_name gin_trgm_ops);
CREATE INDEX buildroot_file_name_idx ON buildroot_file USING btree (file_name);
CREATE INDEX buildroot_file_pkg_idx ON buildroot_file USING btree (package_id);
CREATE INDEX buildroot_pkg_name_gin_idx ON buildroot_pkg USING gin (name gin_trgm_ops);
CREATE INDEX buildroot_pkg_name_idx ON buildroot_pkg USING btree (name);

/* UBUNTU */

CREATE TABLE ubuntu_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT ubuntu_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE ubuntu_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT ubuntu_file_pk PRIMARY KEY (id)
);

COPY ubuntu_pkg FROM '/tmp/pg_deploy/tables/ubuntu/ubuntu_pkg.csv' CSV HEADER;
COPY ubuntu_file FROM '/tmp/pg_deploy/tables/ubuntu/ubuntu_file.csv' CSV HEADER;

CREATE INDEX ubuntu_file_name_gin_idx ON ubuntu_file USING gin (file_name gin_trgm_ops);
CREATE INDEX ubuntu_file_name_idx ON ubuntu_file USING btree (file_name);
CREATE INDEX ubuntu_file_pkg_idx ON ubuntu_file USING btree (package_id);
CREATE INDEX ubuntu_pkg_name_gin_idx ON ubuntu_pkg USING gin (name gin_trgm_ops);
CREATE INDEX ubuntu_pkg_name_idx ON ubuntu_pkg USING btree (name);

/* OPENWRT */

CREATE TABLE openwrt_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT openwrt_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE openwrt_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT openwrt_file_pk PRIMARY KEY (id)
);

COPY openwrt_pkg FROM '/tmp/pg_deploy/tables/openwrt/openwrt_pkg.csv' CSV HEADER;
COPY openwrt_file FROM '/tmp/pg_deploy/tables/openwrt/openwrt_file.csv' CSV HEADER;

CREATE INDEX openwrt_file_name_gin_idx ON openwrt_file USING gin (file_name gin_trgm_ops);
CREATE INDEX openwrt_file_name_idx ON openwrt_file USING btree (file_name);
CREATE INDEX openwrt_file_pkg_idx ON openwrt_file USING btree (package_id);
CREATE INDEX openwrt_pkg_name_gin_idx ON openwrt_pkg USING gin (name gin_trgm_ops);
CREATE INDEX openwrt_pkg_name_idx ON openwrt_pkg USING btree (name);

/* ALPINE */

CREATE TABLE alpine_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT alpine_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE alpine_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT alpine_file_pk PRIMARY KEY (id)
);

COPY alpine_pkg FROM '/tmp/pg_deploy/tables/alpine/alpine_pkg.csv' CSV HEADER;
COPY alpine_file FROM '/tmp/pg_deploy/tables/alpine/alpine_file.csv' CSV HEADER;

CREATE INDEX alpine_file_name_gin_idx ON alpine_file USING gin (file_name gin_trgm_ops);
CREATE INDEX alpine_file_name_idx ON alpine_file USING btree (file_name);
CREATE INDEX alpine_file_pkg_idx ON alpine_file USING btree (package_id);
CREATE INDEX alpine_pkg_name_gin_idx ON alpine_pkg USING gin (name gin_trgm_ops);
CREATE INDEX alpine_pkg_name_idx ON alpine_pkg USING btree (name);

/* OPENEMBEDDED */

CREATE TABLE openembedded_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT openembedded_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE openembedded_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT openembedded_file_pk PRIMARY KEY (id)
);

COPY openembedded_pkg FROM '/tmp/pg_deploy/tables/openembedded/openembedded_pkg.csv' CSV HEADER;
COPY openembedded_file FROM '/tmp/pg_deploy/tables/openembedded/openembedded_file.csv' CSV HEADER;

CREATE INDEX openembedded_file_name_gin_idx ON openembedded_file USING gin (file_name gin_trgm_ops);
CREATE INDEX openembedded_file_name_idx ON openembedded_file USING btree (file_name);
CREATE INDEX openembedded_file_pkg_idx ON openembedded_file USING btree (package_id);
CREATE INDEX openembedded_pkg_name_gin_idx ON openembedded_pkg USING gin (name gin_trgm_ops);
CREATE INDEX openembedded_pkg_name_idx ON openembedded_pkg USING btree (name);

/* PTXDIST_DISTROKIT */

CREATE TABLE ptxdist_distrokit_pkg (
	id serial8 NOT NULL,
	name varchar NOT NULL,
	CONSTRAINT ptxdist_distrokit_pkg_pk PRIMARY KEY (id)
);

CREATE TABLE ptxdist_distrokit_file (
	id serial8 NOT NULL,
	file_name varchar NOT NULL,
	"location" varchar NOT NULL,
	package_id int8 not NULL,
	CONSTRAINT ptxdist_distrokit_file_pk PRIMARY KEY (id)
);

COPY ptxdist_distrokit_pkg FROM '/tmp/pg_deploy/tables/ptxdist_distrokit/ptxdist_distrokit_pkg.csv' CSV HEADER;
COPY ptxdist_distrokit_file FROM '/tmp/pg_deploy/tables/ptxdist_distrokit/ptxdist_distrokit_file.csv' CSV HEADER;

CREATE INDEX ptxdist_distrokit_file_name_gin_idx ON ptxdist_distrokit_file USING gin (file_name gin_trgm_ops);
CREATE INDEX ptxdist_distrokit_file_name_idx ON ptxdist_distrokit_file USING btree (file_name);
CREATE INDEX ptxdist_distrokit_file_pkg_idx ON ptxdist_distrokit_file USING btree (package_id);
CREATE INDEX ptxdist_distrokit_pkg_name_gin_idx ON ptxdist_distrokit_pkg USING gin (name gin_trgm_ops);
CREATE INDEX ptxdist_distrokit_pkg_name_idx ON ptxdist_distrokit_pkg USING btree (name);

/* NSRL RDS */

CREATE TABLE nsrl_file (
	file_name varchar NOT NULL,
	file_id serial8 NOT NULL,
	CONSTRAINT nsrl_file_pk PRIMARY KEY (file_id)
);

COPY nsrl_file FROM '/tmp/pg_deploy/tables/nsrl/nsrl_file.csv' CSV HEADER;

CREATE INDEX nsrl_file_name_gin_idx ON nsrl_file USING gin (file_name gin_trgm_ops);
CREATE INDEX nsrl_file_name_idx ON nsrl_file USING btree (file_name);

REINDEX DATABASE CONCURRENTLY;

CREATE ROLE juicepress LOGIN PASSWORD 'juicepress';
GRANT CONNECT ON DATABASE juicepress TO juicepress;
GRANT USAGE ON SCHEMA public TO juicepress;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO juicepress;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO juicepress;
