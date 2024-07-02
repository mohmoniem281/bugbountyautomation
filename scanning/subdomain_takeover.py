from asyncio.subprocess import PIPE
from concurrent.futures import process
from dataclasses import dataclass
import os
from re import sub
import sys
import argparse
import mysql.connector
import subprocess
import asyncio

program_id=""
db_name=""
db_host=""
db_pass=""
db_user=""
subdomains=[]
subdomains_file=""
processing_folder=""
files=[]
subjack_tool=""
final_file_name=""
subjack_fingerprint=""

def setup():
    global program_id,db_name,db_host,db_pass,db_user,processing_folder,subjack_tool,final_file_name,subjack_fingerprint

    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-processingfolder')
    par.add_argument('-subjack')
    par.add_argument('-finalfilename')
    par.add_argument('-subjackfingerprint')

    args = par.parse_args()
    program_id = args.program
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    processing_folder = args.processingfolder
    subjack_tool = args.subjack
    final_file_name = args.finalfilename
    subjack_fingerprint = args.subjackfingerprint


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

async def subjack(subdomains_file):
    global files
    file=processing_folder+final_file_name
    proc= await asyncio.create_subprocess_shell(subjack_tool + " -w "+subdomains_file+" -o " +file+" -c "+ subjack_fingerprint+" -ssl",stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def run_all():
    print(" [+] Queuing subdomain takeover tasks.")
    print(" [+] Preparing subjack tasks.")
    tasks=[]
    tasks.append(asyncio.create_task(subjack(subdomains_file)))
    await asyncio.wait(tasks)



if __name__ == "__main__":
    setup()
    get_subdomains()
    print(" [+] Checking for subdomains takover.")
    asyncio.run(run_all())
    print(" [+] Completed checking. Output "+processing_folder+final_file_name)
    print("============================================================")

