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
amassconfig=""
root_domain=""
asns=[]
processing_folder=""
processes=[]
files=[]
final_file_name = ""

def setup():
    global program_id,db_name,db_host,db_pass,db_user,amassconfig,root_domain,processing_folder,final_file_name
    
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-amassconfig')
    par.add_argument('-domain')
    par.add_argument('-processingfolder')
    par.add_argument("-finalfilename")

    args = par.parse_args()
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    amassconfig = args.amassconfig
    program_id = args.program
    root_domain = args.domain
    processing_folder = args.processingfolder
    final_file_name = args.finalfilename

def getASNs():
    global asns
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    cur = db.cursor()
    query = "select asn from asns where program_id = "+str(program_id)
    cur.execute(query)
    asns = cur.fetchall()
    db.close()


async def amass(asn):
    print(" [+] Processing "+str(asn))
    global files
    file = processing_folder+"root_domains_from_asns_"+asn+"_amass.txt"
    files.append(file)
    # processes.append(subprocess.Popen(["amass"+ " intel"+ " -asn "+asn+" -whois "+" -d "+ root_domain + " -config "+amassconfig+" | "+" anew "+file],shell=True))
    proc= await asyncio.create_subprocess_shell("amass"+ " intel"+ " -asn "+asn+" -whois "+" -d "+ root_domain + " -config "+amassconfig+" | "+" anew "+file,stdout=PIPE)
    await proc.communicate()
    print (" [+] Completed "+str(asn))


async def combine_results():
    final_file = processing_folder + final_file_name
    for file in files:
        proc= await asyncio.create_subprocess_shell("cat "+ file +" | anew " + final_file,stdout=PIPE)
        await proc.communicate()
        os.rename(os.path.abspath(file),os.path.abspath(file)+".AGGREGATED")
    

#.popen allows parallel
#.call blocks until finished
async def amass_all():
    global asns
    tasks=[]
    for asn, in asns:
        tasks.append(asyncio.create_task(amass(asn)))
  
    await asyncio.wait(tasks) 
    await combine_results()

if __name__ == "__main__":
    setup()
    getASNs()
    print(" [+] Processing amass.")
    asyncio.run(amass_all())
    print(" [+] Completed processing amass. Output "+processing_folder+final_file_name)
    print("============================================================")
    

    
    
    





    