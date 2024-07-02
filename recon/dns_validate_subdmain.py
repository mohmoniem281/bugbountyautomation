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
list_location=""
output_file_name=""
pure_dns_location=""
files = []
nameserver_list=""


def setup():

    global program_id,processing_folder,list_location,output_file_name,pure_dns_location,nameserver_list

    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-listlocation')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfilename')
    par.add_argument('-purednslocation')
    par.add_argument('-nameserverlist')

    args = par.parse_args()
    processing_folder = args.processingfolder
    list_location = args.listlocation
    output_file_name = args.outputfilename
    pure_dns_location = args.purednslocation
    nameserver_list = args.nameserverlist




async def pure_dns(input_file):
    file = os.path.join(processing_folder,output_file_name)
    input_file_full_path = os.path.join(processing_folder,input_file)
    proc = await asyncio.create_subprocess_shell(pure_dns_location+" -r "+nameserver_list+" resolve "+input_file_full_path+" | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(pure_dns(list_location)))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    print(" [+] Validating list with dns. "+list_location)
    asyncio.run(run_all())
    print(" [+] Completed validation. Output "+processing_folder+output_file_name)
    print("============================================================")
