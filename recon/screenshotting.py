from asyncio.subprocess import PIPE
from concurrent.futures import process
import os
import sys
import argparse
import mysql.connector
import subprocess
import asyncio

program_id=""
processing_folder = ""
aquatone_tool=""
output_folder_name=""
subdomains_file_names=""
files=[]
db_name=""
db_host=""
db_pass=""
db_user=""
subdomains_file=""

def setup():

    global program_id,processing_folder,aquatone_tool,output_folder_name,db_name,db_host,db_pass,db_user
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-aquatone')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfolder')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')

    args = par.parse_args()
    processing_folder = args.processingfolder
    aquatone_tool = args.aquatone
    output_folder_name = args.outputfolder
    program_id = args.program
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser

def get_subdomains():
    global subdomains, subdomains_file
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    cur = db.cursor()
    query = "select subdomain from subdomains where (is_live is not null or is_https_live is not null) and program_id = "+str(program_id)
    cur.execute(query)
    subdomains = cur.fetchall()
    db.close()
    all_subdomains=""
    for subdomain, in subdomains:
        all_subdomains+=subdomain
        all_subdomains+="\n"
    all_subdomains = all_subdomains.rstrip("\n")
    with open (os.path.join(processing_folder,"live_subdomains.txt"),'w') as f:
        f.write(all_subdomains)
        f.flush()
        f.close()
    subdomains_file = os.path.join(processing_folder,"live_subdomains.txt")

async def aquatone():
    global files
    folder = os.path.join(processing_folder,output_folder_name)
    proc = await asyncio.create_subprocess_shell("cat " +subdomains_file+" | " +aquatone_tool+" -out "+folder,stdout=PIPE)
    await proc.communicate()
    files.append(folder)
    

async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(aquatone()))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    print(" [+] Retrieving subdomains")
    get_subdomains()
    print(" [+] Screenshotting subdomains "+subdomains_file)
    asyncio.run(run_all())
    print(" [+] Completed Screenshotting Subdomains . Output "+processing_folder+output_folder_name)
    print("============================================================")