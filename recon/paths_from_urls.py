from asyncio.subprocess import PIPE
from copy import copy
import os
import argparse
import asyncio
import mysql.connector

program_id=""
processing_folder = ""
unfurl_tool=""
output_file_name=""
input_file_name=""
files=[]
unfurl_command=""
input_file_full_path = ""
file = ""
db_name=""
db_host=""
db_pass=""
db_user=""
subdomains=[]
def setup():

    global program_id,processing_folder,output_file_name,input_file_name,unfurl_command,input_file_full_path,file,unfurl_tool,db_name,db_host,db_pass,db_user
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-unfurl')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfilename')
    par.add_argument('-inputfilename')
    par.add_argument('-unfurlcommand')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')

    args = par.parse_args()
    unfurl_tool = args.unfurl
    processing_folder = args.processingfolder
    output_file_name = args.outputfilename
    program_id = args.program
    input_file_name = args.inputfilename
    unfurl_command = args.unfurlcommand
    input_file_full_path = os.path.join(processing_folder,input_file_name)
    file = os.path.join(processing_folder,output_file_name)
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
    query = "select subdomain from subdomains where (is_live is not null or is_https_live is not null) and program_id = "+str(program_id)
    cur.execute(query)
    subdomains = cur.fetchall()
    db.close()

async def unfurl():
    global files
    #get paths
    proc = await asyncio.create_subprocess_shell("cat " +input_file_full_path+" | " +unfurl_tool+" -u paths "+" | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def get_parts_from_paths():
    # https://www.youtube.com/watch?v=W4_QCSIujQ4
    # https://stackoverflow.com/questions/2099471/add-a-prefix-string-to-beginning-of-each-line
    global files
    #get parts from paths
    proc = await asyncio.create_subprocess_shell("cat "+file+ " | sed 's#/#\\n#g' | sort -u | sed -e 's/^/\//'",stdout=PIPE)
    output,error = await proc.communicate()
    #paths parts combinations
    result = output.decode().strip()
    combinations=[]
    results = result.split("\n")
    for r in results:
        if str(r)=="/":
            continue
        for n in results:
            if str(n) =="/":
                continue
            combinations.append(str(r)+str(n))
            combinations.append("\n")
    os.rename(file,file+".PATH_COMBINATIONs_DEFINED.txt")
    with open(file,'w') as combination_file:
        combination_file.writelines(combinations)
        combination_file.flush()
    #append the main paths before it was combined
    proc = await asyncio.create_subprocess_shell("cat "+file+".PATH_COMBINATIONs_DEFINED.txt | anew "+file)
    await proc.communicate()

async def file_per_sub_domain():
    for domain, in subdomains:
        proc = await asyncio.create_subprocess_shell("cp "+file+ " "+os.path.join(processing_folder,"wordlists","contentdiscovery/")+domain,stdout=PIPE)
        await proc.communicate()

async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(unfurl()))
    await asyncio.wait(tasks)
    tasks = []
    tasks.append(asyncio.create_task(get_parts_from_paths()))
    await asyncio.wait(tasks)
    tasks = []
    tasks.append(asyncio.create_task(file_per_sub_domain()))
    await asyncio.wait(tasks)
    
if __name__ == "__main__":
    setup()
    print(" [+] Retrieving subdomains")
    get_subdomains()
    print(" [+] Unfurl-ing file "+processing_folder+input_file_name)
    asyncio.run(run_all())
    print(" [+] Completed Un-furling . Output "+processing_folder+output_file_name)
    print(" [+] Copied results into file for each subdomain in workdlists folder.")
    print("============================================================")