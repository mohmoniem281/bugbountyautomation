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
final_file_name=""
subdomains=[]
subdomains_file=""
httprobe_location=""


def setup():
    global program_id,db_name,db_host,db_pass,db_user,processing_folder,final_file_name,httprobe_location
    
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-processingfolder')
    par.add_argument("-finalfilename")
    par.add_argument("-httprobelocation")

    args = par.parse_args()
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    program_id = args.program
    processing_folder = args.processingfolder
    final_file_name = args.finalfilename
    httprobe_location = args.httprobelocation

def get_subdomains():
    global subdomains,subdomains_file
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    cur = db.cursor()
    query = "select subdomain from subdomains where program_id = "+str(program_id)
    cur.execute(query)
    subdomains = cur.fetchall()
    db.close()
    all_subdomains=""
    for subdomain, in subdomains:
        all_subdomains+=subdomain
        all_subdomains+="\n"
    all_subdomains = all_subdomains.rstrip("\n")
    with open(os.path.join(processing_folder,"subdomains.txt"),'w') as f:
        f.write(all_subdomains)
        f.flush()
        f.close()
    subdomains_file = processing_folder+"subdomains.txt"

async def httprobe():
    file = processing_folder+final_file_name
    proc = await asyncio.create_subprocess_shell("cat "+subdomains_file+" | "+httprobe_location+" | anew "+file,stdout=PIPE)
    await proc.communicate()


async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(httprobe()))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    get_subdomains()
    print(" [+] Validating subdomains with httprobe.")
    asyncio.run(run_all())
    print(" [+] Completed validation. Output "+processing_folder+final_file_name)
    print("============================================================")