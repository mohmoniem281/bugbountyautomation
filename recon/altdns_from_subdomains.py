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
altdns_tool=""
altdns_wordlist=""
subdomains=[]
all_subdomains=""
downloaded_subdomains_file=""
processing_folder=""
altdns_output_results="altdns_output_results.txt"
altdns_output_data = "altdns_output_data.txt"
all_text_mutated_file="all_text_mutated_file.txt"
files=[]
final_file_name=""


def setup():
    global program_id,db_name,db_host,db_pass,db_user,altdns_tool,altdns_wordlist,processing_folder,final_file_name
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-altdnstool')
    par.add_argument('-altdnswordlist')
    par.add_argument('-processingfolder')
    par.add_argument('-finalfilename')

    args = par.parse_args()
    program_id = args.program
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    altdns_tool = args.altdnstool
    altdns_wordlist= args.altdnswordlist
    processing_folder = args.processingfolder
    final_file_name =args.finalfilename

def get_subdomains():
    global subdomains,downloaded_subdomains_file,all_subdomains
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
    for subdomain, in subdomains:
        all_subdomains+=subdomain
        all_subdomains+="\n"
        # all_domains_urls+="https://"
        # all_domains_urls+=domain
        # all_domains_urls+="\n"
    all_subdomains = all_subdomains.rstrip("\n")
    downloaded_subdomains_file = os.path.join(processing_folder,"downloaded_subdomains.txt")
    with open(downloaded_subdomains_file,'w') as f:
        f.write(all_subdomains)
        f.flush()
        f.close()

async def altdns(subdomains_file):
    global files
    # file = processing_folder+"-altdns_subdomains_"+".txt"
    data_file = processing_folder+final_file_name
    proc= await asyncio.create_subprocess_shell(altdns_tool+ " -i "+subdomains_file+" -o "+data_file+ " -w "+altdns_wordlist,stdout=PIPE)
    await proc.communicate()
    files.append(data_file)


async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(altdns(downloaded_subdomains_file)))
    await asyncio.wait(tasks)


if __name__ == "__main__":
    setup()
    #we can have a command line that instructs which tool we want to use
    print(" [+] Retrieving subdomains.")
    get_subdomains()
    print(" [+] Preparing tasks for subdomains from altdns.") 
    asyncio.run(run_all())
    print(" [+] Completed processing Subdomains from alternative names.")
    print("============================================================")


