#!/usr/bin/python3
# -*- coding: utf-8 -*-

##########################################################################################################################
import time
import os
import sys
import logging
import re
import inspect
import argparse
import shutil

# 
# -1: will be handled with customized logic
#  0: schema name = "", for objects should not be used
#  > 0: column number - 1
# 

linesToCheck = [
{'id': 1 , 'ddl': 'CREATE ROLE',             'schema_name_column': 0, 'object_name_column': 3 },
{'id': 2 , 'ddl': 'CREATE TABLESPACE',       'schema_name_column': 0, 'object_name_column': 3 },
{'id': 3 , 'ddl': 'CREATE DATABASE',         'schema_name_column': 0, 'object_name_column': 3 },
{'id': 4 , 'ddl': 'CREATE SCHEMA',           'schema_name_column': 3,  'object_name_column': 3 },
{'id': 5 , 'ddl': 'CREATE EXTENSION',        'schema_name_column': 9,  'object_name_column': 6 },
{'id': 6 , 'ddl': 'CREATE FUNCTION',         'schema_name_column': 3, 'object_name_column': 3 },
{'id': 7 , 'ddl': 'CREATE TEMPORARY TABLE',  'schema_name_column': 0, 'object_name_column': 4 },
{'id': 8 , 'ddl': 'CREATE SEQUENCE',         'schema_name_column': 3, 'object_name_column': 3 },
{'id': 9 , 'ddl': 'CREATE TRIGGER',          'schema_name_column': -1, 'object_name_column': -1 },
{'id': 10 , 'ddl': 'CREATE UNIQUE INDEX',     'schema_name_column': 6,  'object_name_column': 4 },
{'id': 11 , 'ddl': 'CREATE INDEX',            'schema_name_column': 5,  'object_name_column': 3 },
{'id': 12 , 'ddl': 'CREATE UNLOGGED TABLE',   'schema_name_column': 4, 'object_name_column': 4 },
{'id': 13 , 'ddl': 'CREATE VIEW',             'schema_name_column': 3, 'object_name_column': 3 },
{'id': 14 , 'ddl': 'CREATE PROCEDURE',        'schema_name_column': 3, 'object_name_column': 3 },
{'id': 15 , 'ddl': 'CREATE TYPE',             'schema_name_column': 3, 'object_name_column': 3 },
{'id': 16 , 'ddl': 'CREATE TABLE',            'schema_name_column': 3, 'object_name_column': 3 }
]

##########################################################################################################################
def log_it(logLevel, message):
    "Automatically log the current function details."

    logging_levels = {'critical': logging.critical, 'error': logging.error, 'warning': logging.warning, 'info': logging.info, 'debug': logging.debug}

    func = inspect.currentframe().f_back.f_code

    logging_levels[logLevel]("%s in %s:%i -> %s" % (
        func.co_name,
        func.co_filename,
        func.co_firstlineno,
        message
    ))

##########################################################################################################################
def check_dir_exists(directory, forceRecreate=False):
    "pass forceRecreate=True to delete the dir and all its contents in case it already exists"

    global directoriesCreated

    if directory in directoriesCreated:
        return True

    try:
        if os.path.isdir(directory):
            if forceRecreate == True:
                log_it("info", "Removing directory and all its contents: {}".format(directory))
                shutil.rmtree(directory)
                log_it("info", "Creating directory: {}".format(directory))
                os.mkdir(directory)
                directoriesCreated.append(directory)

        else:
            log_it("info", "Creating directory: {}".format(directory))
            os.mkdir(directory)
            directoriesCreated.append(directory)
            
    except Exception as e:
        print("ERROR: Exception occured while creating directory: {}, exception: {}".format(directory, str(e)))
        log_it("critical", "Exception occured while trying to create the directory: {}, exception: {}".format(directory, str(e)))
        sys.exit(1)

##########################################################################################################################
def create_the_patterns():

    global compiledRegexPatterns

    for object in linesToCheck:
        compiledRegexPatterns["{}".format(object["id"])] = re.compile(r"^(\s+)?({})(.+)$".format(object["ddl"]))

##########################################################################################################################
def write_to_file(lineNumber, textLine):
    
    global rootDir
    global linesToCheck
    global currOutputFile
    global currOutputDir
    global currDB
    global currSchema
    global EOLsep
    global totalProcessingErrors
    global timeStart
    global compiledRegexPatterns

    try:
        textLine = textLine[:-1]

        if textLine.find("--") == 0:
            # write to file:
            log_it("debug", "line: {} >--------> SKIPPED".format(textLine))
            return True

        for pgDDLcommand in linesToCheck:

            # find if we have a CREATE xxx line:
            matches = re.search(compiledRegexPatterns["{}".format(pgDDLcommand["id"])], textLine)
            if matches is not None:
                log_it("debug", "Line {}: its a create object command: {}".format(lineNumber, pgDDLcommand))

                # remove the potential leading/trailing whitespace:
                textLine = textLine.strip()

                # 3 commands with unique logic:
                if pgDDLcommand['ddl'] == "CREATE TRIGGER":
                    if textLine.split(" ").index("FOR") == textLine.split(" ").index("EACH") - 1:
                        currSchema = textLine.split(" ")[textLine.split(" ").index("FOR") - 1]
                        objectName = textLine.split(" ")[2]
                        currOutputDir = rootDir + "/" + currDB + "/" + currSchema

                    else:
                        log_it("error", "Line {}: Could not determine the schema name from this line. Skipping..".format(lineNumber))
                        totalProcessingErrors += 1
                        return False

                elif pgDDLcommand['ddl'] == "CREATE DATABASE":
                    currDB = textLine.split(" ")[2]
                    currOutputDir = rootDir + "/" + currDB + "/"

                elif pgDDLcommand['ddl'] == "CREATE SCHEMA":
                    currSchema = textLine.split(" ")[2].replace(";", "")
                    currOutputDir = rootDir + "/" + currDB + "/" + currSchema

                # determine schema name:
                if pgDDLcommand['schema_name_column'] == -1:
                    pass

                elif pgDDLcommand['schema_name_column'] == 0:
                    currSchema = ""

                elif pgDDLcommand['schema_name_column'] > 0:
                    currSchema = textLine.split(" ")[pgDDLcommand['schema_name_column'] - 1].replace(";", "") # .split(".")[0].replace(";", "").split("(")[0]
                
                elif pgDDLcommand['object_name_column'] > 0:
                    currSchema = textLine.split(" ")[pgDDLcommand['object_name_column'] - 1].replace(";", "") # .split(".")[0].replace(";", "").split("(")[0]

                else:
                    log_it("error", "Line {}: Could not determine the schema name from this line. Skipping..".format(lineNumber))
                    totalProcessingErrors += 1
                    return False

                if (len(currSchema.split(".")) == 2):
                    currSchema = currSchema.split(".")[0]            

                # determine object name:
                if pgDDLcommand['object_name_column'] == -1:
                    pass

                elif pgDDLcommand['object_name_column'] > 0:
                    objectName = textLine.split(" ")[pgDDLcommand['object_name_column'] - 1].replace(";", "") # .split(".")[1].replace(";", "").split("(")[0]
                
                elif pgDDLcommand['schema_name_column'] > 0:
                    objectName = textLine.split(" ")[pgDDLcommand['schema_name_column'] - 1].replace(";", "") # .split(".")[1].replace(";", "").split("(")[0]

                else:
                    log_it("error", "Line {}: Could not determine the object name from this line. Skipping..".format(lineNumber))
                    totalProcessingErrors += 1
                    return False

                if (len(currSchema.split(".")) == 2):
                    currSchema = currSchema.split(".")[0]

                if (len(objectName.split(".")) == 2):
                    objectName = objectName.split(".")[1]

                objectName = objectName.replace(";", "").split("(")[0]


                # finalizing processing:
                log_it("debug", "Line {}: currSchema: {}, objectName: {}".format(lineNumber, currSchema, objectName))
                currOutputDir = rootDir + "/" + currDB + "/" + currSchema
                currOutputFile = pgDDLcommand['ddl'].replace("CREATE ", "").replace(" ", "_") + "_" + objectName + ".sql"
                log_it("debug", "Line {}: currOutputFile: {}".format(lineNumber, currOutputDir + "/" + currOutputFile))
                
                # needs a break here!
                break

        # check if dir exists:
        check_dir_exists(currOutputDir)

        # write to file:
        log_it("debug", "line {}: {} >--------> file: {}".format(lineNumber, textLine, currOutputDir + "/" + currOutputFile))
        with open(currOutputDir + '/' + currOutputFile, "a") as fp:
            fp.write("{}{}".format(textLine, EOLsep))
            fp.close()

    except Exception as e:
        print("ERROR: Exception occured while processing line: {}, exception: {}".format(lineNumber, str(e)))
        log_it("critical", "Exception during processing line: {}, exception: {}".format(lineNumber, str(e)))
        totalProcessingErrors += 1
        return False

    return True

##########################################################################################################################
timeStart = time.time()

# init vars:
dumpFile = ""
rootDir = ""
EOLsep = "\n" # "\r\n" for win, "\n" for linux
currOutputFile = "PGcluster.sql"
currOutputDir = ""
currDB = "postgres"
currSchema = ""
totalProcessingErrors = 0
updateStatusAfterLines = 5000
directoriesCreated = []
compiledRegexPatterns = {}

##########################################################################################################################
def main():
    
    global currOutputFile
    global currDB
    global currSchema
    global dumpFile
    global rootDir
    global currOutputDir
    global updateStatusAfterLines
    linesToUpdateUser = 1

    parser = argparse.ArgumentParser()
    parser.add_argument('--dumpfile', help='the Postgres dump file to process', type=str, dest="dumpFile", required=True)
    parser.add_argument('--loglevel', help='the logging level (default=debug)', type=str, dest="logLevel", required=False, default="debug")
    args = parser.parse_args()

    dumpFile = args.dumpFile
    logLevel = args.logLevel

    if os.path.isfile(dumpFile) == False:
        print("ERROR: Postgres dump file provided: {} was not found. Exiting..".format(dumpFile))
        sys.exit(1)

    rootDir = "results" + "/" + ('').join(dumpFile.split('.')[:-1])
    currOutputDir = rootDir

    # create the dirs:
    check_dir_exists("log")
    check_dir_exists("results")
    check_dir_exists(rootDir, True)

    logging.getLogger('').handlers = []
    logging_levels = {'critical': logging.CRITICAL, 'error': logging.ERROR, 'warning': logging.WARNING, 'info': logging.INFO, 'debug': logging.DEBUG}
    logging.basicConfig(filename="log/" + ('').join(dumpFile.split('.')[:-1]) + ".log", level=logging_levels[logLevel], format="%(asctime)s - %(levelname)s - %(message)s", filemode='w')

    create_the_patterns()

    try:
        with open(dumpFile, "r") as fp:
            currlineTxt = fp.readline()
            currLineCnt = 1
            
            while currlineTxt:
                # print("Line {}: {}".format(currLineCnt, currlineTxt.strip("\n")))				
                processingResult = write_to_file(currLineCnt, currlineTxt)

                if linesToUpdateUser == updateStatusAfterLines:
                    timeNow = time.time()
                    print("> Processed {} lines. Processing errors: {}, elapsed time: {} seconds.".format(currLineCnt, totalProcessingErrors, format(timeNow - timeStart, '.3g')))
                    linesToUpdateUser = 0

                currlineTxt = fp.readline()
                linesToUpdateUser += 1
                currLineCnt += 1

    except Exception as e:
        log_it("critical", "Exception during parsing the dump file: {}, exception: {}".format(dumpFile, str(e)))
        sys.exit(1)

    timeEnd = time.time()
    print("> Processing complete. Processed {} lines. Processing errors: {}, elapsed time: {} seconds.".format(currLineCnt, totalProcessingErrors, format(timeEnd - timeStart, '.3g')))
    print("  Results at directory: {}".format(rootDir))

##########################################################################################################################
# python3 check:
if sys.version_info.major < 3:
    print("ERROR: This tool requires Python 3. Exiting..")
    sys.exit(0)

# start:
if __name__ == '__main__':
    main()
