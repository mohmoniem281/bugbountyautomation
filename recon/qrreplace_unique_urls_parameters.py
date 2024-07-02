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
qreplace_tool=""
output_file_name=""
input_file_name=""
files=[]

def setup():

    global program_id,processing_folder,qreplace_tool,output_file_name,input_file_name
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-qreplace')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfilename')
    par.add_argument('-inputfilename')

    args = par.parse_args()
    processing_folder = args.processingfolder
    qreplace_tool = args.qreplace
    output_file_name = args.outputfilename
    program_id = args.program
    input_file_name = args.inputfilename

async def qrreplace():
    global files
    file = os.path.join(processing_folder,output_file_name)
    input_file_full_path = os.path.join(processing_folder,input_file_name)
    proc = await asyncio.create_subprocess_shell("cat " +input_file_full_path+" | " +qreplace_tool+" -a "+" | anew "+file,stdout=PIPE)
    await proc.communicate()
    files.append(file)

async def run_all():
    tasks=[]
    tasks.append(asyncio.create_task(qrreplace()))
    await asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    print(" [+] Removing urls and parameters combination duplicates from "+processing_folder+output_file_name)
    asyncio.run(run_all())
    print(" [+] Completed removing urls and parameters combination duplicates . Output "+processing_folder+output_file_name)
    print("============================================================")