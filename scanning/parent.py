import argparse
import json
import os
import subprocess
from sys import stdout
import asyncio
from asyncio.subprocess import PIPE

settings={}
program_id=""
subdomain_takeover_filename="subdomain_takeover.txt"

def loadSettings():
    global settings
    with open("settings.json",'r') as settings_file:
        settings = json.load(settings_file)

def setup():
    global program_id,root_domain
    par = argparse.ArgumentParser()
    par.add_argument('-program')

    args = par.parse_args()
    program_id = args.program

async def subdomain_takeover():
    proc= await asyncio.create_subprocess_exec(
        "python3",settings["subdomain_takeover_script_path"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],
        "-processingfolder",settings["results_folder"],
        "-subjack",settings["subjack"],
        "-finalfilename",subdomain_takeover_filename,
        "-subjackfingerprint",settings["subjack_fingerprint"]
    )
    await proc.wait()

async def sync_to_server(operation,file):
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["sync_to_server_script"],
        "-programid" ,program_id,
        "-operation",operation,
        "-inputfile",file,
        "-dbname",settings["dbname"],
        "-dbhost",settings["dbhost"],
        "-dbuser",settings["dbuser"],
        "-dbpass",settings["dbpass"],
        "-awsaccesskey",settings['aws_s3_access_key'],
        "-awssecretkey",settings['aws_s3_secret_key'],
        "-bucketname",settings['bucket_name']
    )
    await proc.wait()


async def main():
    input("[+] Press enter to run subdomain takover.")
    print ("[+] Executing subdomain takeover.")
    subdomain_takeover_task = asyncio.create_task(subdomain_takeover())
    await asyncio.wait((subdomain_takeover_task,))
    if input("[+] Completed executing subdomain takeover. Sync to server? [y/n]").lower()=="y":
        print("[+] Syncing to server.")
        await sync_to_server("subdomain_takeover",settings['results_folder']+subdomain_takeover_filename)
        print("[+] Syncing completed.")
    print("========================================================================================================================")



if __name__ == "__main__":
    loadSettings()
    setup()
    asyncio.run(main())