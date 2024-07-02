from asyncio.subprocess import PIPE
from concurrent.futures import process
import os
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
processing_folder=""
subdomains_file=""
final_file_name=""
gau_tool=""
hakrawler_tool=""
hakrawler_proxy=""
files=[]

def setup():
    global program_id,db_name,db_host,db_pass,db_user,processing_folder,final_file_name,gau_tool,hakrawler_tool,hakrawler_proxy

    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-processingfolder')
    par.add_argument('-finalfilename')
    par.add_argument('-gautool')
    par.add_argument('-hakrawler')
    par.add_argument('-hakrawlerproxy')

    args = par.parse_args()
    program_id = args.program
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    processing_folder = args.processingfolder
    final_file_name = args.finalfilename
    gau_tool = args.gautool
    hakrawler_tool = args.hakrawler
    hakrawler_proxy = args.hakrawlerproxy

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

async def gau():
    file = processing_folder+"_gau_subdomains_.txt"
    proc = await asyncio.create_subprocess_shell("cat "+subdomains_file+" | "+ gau_tool + " | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def hakrawler():
    file = processing_folder+"_hakrawler_subdomains_.txt"
    proc=""
    if hakrawler_proxy =="":
        proc = await asyncio.create_subprocess_shell("cat "+subdomains_file+" | "+ hakrawler_tool + " | anew "+file,stdout=PIPE)
    else:
        proc = await asyncio.create_subprocess_shell("cat "+subdomains_file+" | "+ hakrawler_tool + " -proxy "+hakrawler_proxy+" | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def run_all():
    print (" [+] Queueing all tasks.")
    print(" [+] Preparing gau,hakrawler.")
    tasks=[]
    tasks.append(asyncio.create_task(gau()))
    tasks.append(asyncio.create_task(hakrawler()))
    await asyncio.wait(tasks)

async def combine_results():
    print(" [+] Combining results to "+processing_folder+final_file_name)
    output = processing_folder+final_file_name
    for file in files:
        proc = await asyncio.create_subprocess_shell("cat "+file+" | anew "+output,stdout=PIPE)
        await proc.communicate()
        os.rename(os.path.abspath(file),os.path.abspath(file)+".AGGREGATED")

if __name__ == "__main__":
    setup()
    #we can have a command line that instructs which tool we want to use
    print(" [+] Retrieving subdomains")
    get_subdomains()
    print(" [+] Preparing tasks for urls from subdomains.") 
    asyncio.run(run_all())
    asyncio.run(combine_results())
    print(" [+] Completed processing urls from subdomains.")
    print("============================================================")

