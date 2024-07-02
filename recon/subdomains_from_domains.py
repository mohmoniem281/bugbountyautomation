from asyncio.subprocess import PIPE
from concurrent.futures import process, thread
import os
from random import gauss
import sys
import argparse
import mysql.connector
import subprocess
import asyncio
import time



program_id=""
db_name=""
db_host=""
db_pass=""
db_user=""
amassconfig=""
domains=[]
processing_folder=""
shosubgo_tool=""
shodan_key=""
files=[]
subdomainizer_tool=""
subscraper_tool=""
tasks=[]
final_file_name=""
domains_file=""
domains_url_file=""
gau_tool = ""
github_tool=""
github_token=""
new_discovered_domains_file = "new_discovered_domains_file.txt"
filtered_sub_domains_file = "filtered_sub_domains_file.txt"

def setup():
    global program_id,db_name,db_host,db_pass,db_user,amassconfig,processing_folder,shosubgo_tool,shodan_key,subdomainizer_tool,subscraper_tool,final_file_name,gau_tool,github_tool,github_token
    
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-amassconfig')
    par.add_argument('-processingfolder')
    par.add_argument('-shosubgo')
    par.add_argument('-shodankey')
    par.add_argument('-subdomainizer')
    par.add_argument('-subscraper')
    par.add_argument("-finalfilename")
    par.add_argument("-gautool")
    par.add_argument("-githubtool")
    par.add_argument("-githubtoken")


    args = par.parse_args()
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    amassconfig = args.amassconfig
    program_id = args.program
    processing_folder = args.processingfolder
    shosubgo_tool = args.shosubgo
    shodan_key = args.shodankey
    shosubgo_tool = args.shosubgo
    shodan_key = args.shodankey
    subdomainizer_tool = args.subdomainizer
    subscraper_tool = args.subscraper
    final_file_name = args.finalfilename
    gau_tool = args.gautool
    github_tool = args.githubtool
    github_token = args.githubtoken

def get_domains():
    global domains,domains_file,domains_url_file,processing_folder
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    cur = db.cursor()
    query = "select domain from domains where program_id = "+str(program_id)
    cur.execute(query)
    domains = cur.fetchall()
    db.close()
    all_domains=""
    # all_domains_urls=""
    for domain, in domains:
        all_domains+=domain
        all_domains+="\n"
        # all_domains_urls+="https://"
        # all_domains_urls+=domain
        # all_domains_urls+="\n"
    all_domains = all_domains.rstrip("\n")
    # all_domains_urls = all_domains_urls.rstrip("\n")
    with open (os.path.join(processing_folder,"root_domains.txt"),'w') as f:
        f.write(all_domains)
        f.flush()
        f.close()
    domains_file = processing_folder+"root_domains.txt"
    #input("[+][+][+] CHECK THE DOMAIN FILE FOR DEBUGGING") #DEBUGGING
    # with open (os.path.join(processing_folder,"root_domains_urls.txt"),'w') as f:
    #     f.write(all_domains_urls)
    #     f.flush()
    #     f.close()
    # domains_url_file = processing_folder+"root_domains_urls.txt"

async def amass(domains_file):
    global files
    #amass is installed in go path
    file = processing_folder+"-amass_subdomains_"+".txt"
    proc= await asyncio.create_subprocess_shell("amass"+ " enum -active"+ " -df "+domains_file+ " -config "+amassconfig+" | "+" anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def shosubgo(domain):
    file = processing_folder+"-shosubgo_subdomains_"+domain+".txt"
    proc= await asyncio.create_subprocess_shell(shosubgo_tool+ " -d "+domain+ " -s "+shodan_key+" | grep -o -E '[a-z0-9]+\.[a-z]+\.*[a-z]+' | "+" anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def subdomainizer(domains_urls_file_):
    file  = processing_folder+"_subdomainizer_"+".txt"
    #proc = await asyncio.create_subprocess_shell("python3 "+subdomainizer_tool+" -l "+domains_urls_file_ + " | grep -E '[a-z0-9]+\.[a-z]+\.*[a-z]+'"+" | "+" anew "+file,stdout=PIPE)
    proc = await asyncio.create_subprocess_shell("python3 "+subdomainizer_tool+" -l "+domains_urls_file_ + " -o "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def subscraper(domains_file):
    file = processing_folder+"_subscarper_"+".txt"
    proc = await asyncio.create_subprocess_shell("python3 "+subscraper_tool+" "+domains_file+" -o "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def gau(domains_file):
    global domains
    file = processing_folder+"_gau_subdomains_.txt"
    proc = await asyncio.create_subprocess_shell("cat "+domains_file+" | "+ gau_tool + " | grep -o -E '[a-z0-9]+\.[a-z]+\.*[a-z]+'" + " | anew "+file,stdout=PIPE)
    await proc.communicate()
    #clean up
    clean_subdomains=""
    domains_list_from_file=[]
    with open(file,'r')as r:
        domains_list_from_file = r.readlines()
    for subdomain in domains_list_from_file:
        if subdomain.count('.')>0: #making sure it is a subdomain
            split= subdomain.split('.')
            domain = split[len(split)-2]+"."+split[len(split)-1]
            if (domain in domains): #making sure it is one of our domains
                clean_subdomains+=subdomain
    clean_subdomains.rstrip("\n")
    with open(file,'w') as d:
        d.write(clean_subdomains)
        d.flush()
        d.close()
    files.append(file) 

async def github(domain):
    file = processing_folder+"_github_"+domain+".txt"
    proc = await asyncio.create_subprocess_shell("python3 "+github_tool+" -t "+github_token+" -d "+domain+" | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)



async def run_all(domains):
    #FOR NOW WE ARE RUNNING 50 TASKS AT A TIME SINCE THIS IS RUNNING ON MY LOCAL
    print (" [+] Queueing all tasks.")
    global tasks
    print(" [+] Preparing Amass,shosubgo,subscraper,gau tasks.")

    #below logic is to stagger execution  by 50 since we are running on local
    staggered_tasks=[]
    staggered_number=100000
    staggered_tasks.append(asyncio.create_task(amass(domains_file)))  #amass has only one task since it accepts the recussion included
    staggered_tasks.append(asyncio.create_task(subscraper(domains_file)))
    staggered_tasks.append(asyncio.create_task(gau(domains_file)))
    for domain, in domains:

        if len(staggered_tasks)%staggered_number==0 and len(staggered_tasks)>0:
            await asyncio.wait(staggered_tasks)
            staggered_tasks=[]

        staggered_tasks.append(asyncio.create_task(shosubgo(domain)))

    #here in case the loop finished with tasks remainign in queue
    if len(staggered_tasks) > 0:
        await asyncio.wait(staggered_tasks)

async def combine_results():
    print(" [+] Combining results to "+processing_folder+final_file_name)
    output = processing_folder+final_file_name
    for file in files:
        proc = await asyncio.create_subprocess_shell("cat "+file+" | anew "+output,stdout=PIPE)
        await proc.communicate()
        os.rename(os.path.abspath(file),os.path.abspath(file)+".AGGREGATED")

# async def get_new_domains_and_subdomains():
#     final_file = processing_folder+final_file_name
#     domains_file = processing_folder+new_discovered_domains_file
#     subdomains_file = processing_folder+filtered_sub_domains_file
#     proc = await asyncio.create_subprocess_shell("cat "+final_file+" | grep -o -E '^[^.]+\.([^.]+\.)+[^.]*$'"+" | "+" anew "+subdomains_file,stdout=PIPE) #subdomains
#     await proc.communicate()
#     proc = await asyncio.create_subprocess_shell("cat "+final_file+" | grep -v -o -E '^[^.]+\.([^.]+\.)+[^.]*$'"+" | "+" anew "+domains_file,stdout=PIPE) #other than subdomains (usually only domains)
#     await proc.communicate()


if __name__ == "__main__":
    setup()
    #we can have a command line that instructs which tool we want to use
    print(" [+] Retrieving domains")
    get_domains()
    print(" [+] Preparing tasks for Subdomains from domains.") 
    asyncio.run(run_all(domains))
    asyncio.run(combine_results())
    print(" [+] Completed processing Subdomains from domains.")
    print("============================================================")

    









