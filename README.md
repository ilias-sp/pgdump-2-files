## > Introduction

This Python script will process a Postgres Database dump file and split the DML statements it includes to one file per object. It will create a filesystem structure in accordance with the database object hierarchy, for example:

```
Cluster_name \ Database_Name1 \ Schema_name1 \ Object_Name1.sql
                              |              \ Object_Name2.sql
                              |               ..
                              |              \ Object_Name44.sql
                              \ Schema_name2 \ Object_Name1.sql
                                             \ Object_Name2.sql
                                             \ Object_Name3.sql
                                             ..
                                             \ Object_Name99.sql
...
```

Dumping a Postgres database cluster to a dumpfile using `pg_dumpall` is a convenient tool in order to backup the schema definitions, and also compare between different installations or snapshots of the same DB taken at a different time.
The problem is that the `pg_dumpall` will not dump the objects in the same order, and comparing/inspecting these huge files can be a headache.


For more information on how it works, please see below the [Various Notes](#various-notes) section.

---
## > Requirements

To run the tool you will need `Python 3`, along with the below required python packages:

```python
import time
import os
import sys
import logging
import re
import inspect
import argparse
import shutil
```

---
## > How to extract a dump from your database and process it with the tool

1. To dump your database, you should use the `postgres` DB account.
By default Postgres configuration, if you execute the `pg_dumpall` command from the database host you will not be required to provide password, as an example a command would be:

```bash
pg_dumpall -U postgres --schema-only > postgres_db_schema_only.dump
```

The parameter `--schema-only` will extract the object definitions and skip the data.


2. transfer the generated file to the directory of the tool and:

```
./pgdump2files.py --dumpfile postgres_db_schema_only.dump
```

There will be output on screen to inform about the progress. In the end, a log file will be created under `log` directory and the generated filesystem structure with the sql files under `results` directory.

---
## > Various Notes

- The script will parse line by line the dump file, try to detect any `CREATE ` DML statements, and according to rules, decide how to extract the Database, Schema and Object name the line refers to. With this information, will write the line and all the following ones until the next `CREATE ` line to a single file.
- It has been noticed in my dumps, that they sometimes contain DML lines with leading whitespace characters before the `CREATE ` clause, seems to happen pretty often with the `CREATE TEMPORARY TABLE` statements in particular. The code was enhanced to support this scenario (using compiled regex patterns), with an unavoidable downside of additional processing time.
- Lines that are pure comments (starting with `--`) are ignored.
- The tool will create the results under a folder called  under `results/` directory. if this directory alredy exists (i.e. the dump file has already been processed in the past), it will remove it and its contents. Same applies for the log file under `logs/`.
- the logging level is by default on `debug`. You can reduce it to a different level with the argument `--logLevel`.
- It has been delevoped using dumps from Postgres version 11 and 12.
- the DMLs currently supported are:

| DB objects |
| :-------------------------------- |
| CREATE ROLE |
| CREATE TABLESPACE |
| CREATE DATABASE |
| CREATE SCHEMA |
| CREATE EXTENSION |
| CREATE FUNCTION |
| CREATE TEMPORARY TABLE |
| CREATE SEQUENCE |
| CREATE TRIGGER |
| CREATE UNIQUE INDEX |
| CREATE INDEX |
| CREATE UNLOGGED TABLE |
| CREATE VIEW |
| CREATE PROCEDURE |
| CREATE TYPE |
| CREATE TABLE |

---
## > Bugs and Issues

In case you have found a bug, feel free to open an issue!
