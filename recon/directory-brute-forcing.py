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
ffuf_tool=""
output_folder_name=""
files=[]
subdomains = []
db_name=""
db_host=""
db_pass=""
db_user=""

def setup():
    global program_id,processing_folder,ffuf_tool,output_folder_name,db_name,db_host,db_pass,db_user
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-ffuf')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfolder')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')

    args = par.parse_args()
    program_id = args.program
    processing_folder = args.processingfolder
    ffuf_tool = args.ffuf
    output_folder_name = args.outputfolder
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser

def get_subdomains():
    global subdomains
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    cur = db.cursor()
    query = "select subdomain,is_https_live from subdomains where (is_live is not null or is_https_live is not null) and program_id = "+str(program_id)
    cur.execute(query)
    subdomains = cur.fetchall()
    db.close()

async def ffuf(subdomain,is_https):
    global files
    url = "https://"+subdomain
    print(url)
    wordlist = os.path.join(processing_folder,"wordlists","contentdiscovery/" + subdomain)
    output_file_name = os.path.join(processing_folder,"directory-brute-forcing/"+subdomain)
    proc = await asyncio.create_subprocess_shell(ffuf_tool+" -w "+wordlist+" -u "+url+"FUZZ"+" -o "+output_file_name)
    await proc.communicate()

async def run_all():
    tasks=[]
    for subdomain,is_https, in subdomains:
        tasks.append(asyncio.create_task(ffuf(subdomain,is_https)))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    print(" [+] Retrieving subdomains")
    get_subdomains()
    print(" [+] Directory brute forcing subdomains.")
    asyncio.run(run_all())
    print(" [+] Completed directory brute forcing. Output "+processing_folder+"directory-brute-forcing")
    print("============================================================")