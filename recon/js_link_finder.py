from asyncio.subprocess import PIPE, STDOUT
from concurrent.futures import process
import os
import sys
import argparse
import mysql.connector
import subprocess
import asyncio

program_id=""
processing_folder = ""
input_folder=""
files=[]
xnlinkfinder_tool=""
output_folder_name=""

def setup():
    global program_id,processing_folder,xnlinkfinder_tool,output_folder_name
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-xnlinkfinder')
    par.add_argument('-processingfolder')
    par.add_argument('-outputfoldername')

    args = par.parse_args()
    program_id = args.program
    processing_folder = args.processingfolder
    xnlinkfinder_tool = args.xnlinkfinder
    output_folder_name = args.outputfoldername

async def xnlinkfinder(input_file_pointer):
    global files
    output_file_name =os.path.join(processing_folder,"JS","output",os.path.basename(input_file_pointer.name))
    proc = await asyncio.create_subprocess_shell("python3 "+xnlinkfinder_tool+" -i "+ os.path.abspath(input_file_pointer)+" -o "+output_file_name+" -sp https://"+os.path.basename(input_file_pointer.name),STDOUT=PIPE)
    await proc.communicate()

async def run_all():
    tasks=[]
    input_folder = os.path.join(processing_folder,"JS","input")
    for f in os.listdir(input_folder):
        tasks.append(tasks.append(f))
    asyncio.wait(tasks)

if __name__ == "__main__":
    setup()
    print(" [+] Getting JS files.")
    asyncio.run(run_all())
    print(" [+] Completed JS files url extraction.")
    print("============================================================")