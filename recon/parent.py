import argparse
import json
import os
import subprocess
from sys import stdout
import asyncio
from asyncio.subprocess import PIPE

settings={}
program_id=""
root_domain=""
root_domains_from_asns_output_filename="root_domains_from_asns.txt"
root_domains_from_dns_output_filename = "root_domains_from_dns.txt"
subdomains_from_domains_output_filename="subdomains_from_domains.txt"
altdns_from_subdomains_output_filename = "altdns_from_subdomains.txt"
httprobe_on_subdomains_output_filename="httprobe_on_subdomains.txt"
urls_from_subdomains_output_filename="urls_from_subdomains.txt"
urls_from_subdomains_output_filename_duplicates_removed= "urls_from_subdomains_duplicates_removed.txt"
unfurled_urls_paths_brute_force_output_filename = "unfurled_paths_from_urls.txt"
xnlinkfinder_output_filename = "xnlinkfinder.txt"

def loadSettings(): 
    global settings
    with open("settings.json",'r') as settings_file:
        settings = json.load(settings_file)

def setup():
    global program_id,root_domain
    par = argparse.ArgumentParser()
    par.add_argument('-program')
    par.add_argument('-rootdomain')

    args = par.parse_args()
    program_id = args.program
    root_domain=args.rootdomain


async def root_domains_from_asns():
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["root_domains_from_asns_script"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],
        "-amassconfig", settings["amass_config"],
        "-dbhost", settings["dbhost"],
        "-domain", root_domain,
        "-finalfilename",root_domains_from_asns_output_filename,
        "-processingfolder",settings["results_folder"]
    )
    await proc.wait()
    
async def subdomains_from_domains():
    proc=await asyncio.create_subprocess_exec(
        "python3",settings["subdomains_from_domains_script"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],
        "-amassconfig", settings["amass_config"],
        "-processingfolder",settings["results_folder"],
        "-shosubgo",settings["shosubgo_path"],
        "-shodankey",settings["shodan_key"],
        "-subdomainizer",settings["subdomainizer_path"],
        "-subscraper",settings["subscraper_path"],
        "-finalfilename",subdomains_from_domains_output_filename,
        "-gautool",settings["gau_tool"],
        "-githubtool",settings["github_subdomain"],
        "-githubtoken",settings["github_token"]
    )
    await proc.wait()

 
async def altdns_from_subdomains():
    proc=await asyncio.create_subprocess_exec(
        "python3",settings["subdomain_from_altdns_script"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],    
        "-altdnstool",settings["altdns_tool"],
        "-altdnswordlist",settings["altdns_wordlist"],
        "-processingfolder",settings["results_folder"],
        "-finalfilename",altdns_from_subdomains_output_filename
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
        "-dbpass",settings["dbpass"]
    )
    await proc.wait()

async def validate_with_dns(input_file_path,output_file_name):
    proc = await asyncio.create_subprocess_exec(
        "python3", settings["validate_with_dns_script"],
        "-program",program_id,
        "-listlocation",input_file_path,
        "-processingfolder",settings["results_folder"],
        "-outputfilename",output_file_name,
        "-purednslocation",settings["pure_dns_location"],
        "-nameserverlist",settings["nameserver_list_location"]
    )
    await proc.wait()

async def httprobe_on_subdomains(output_file_name):
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["httpprobe_script_location"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],  
        "-processingfolder",settings["results_folder"],
        "-finalfilename",output_file_name,
        "-httprobelocation",settings["httprobe_location"]
    )
    await proc.wait()

async def urls_from_subdomains(output_file_name):
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["urls_from_subdomains_script"],
        "-program",program_id,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"],  
        "-processingfolder",settings["results_folder"],
        "-finalfilename",output_file_name,
        "-gautool",settings["gau_tool"],
        "-hakrawler",settings["hakrawler_tool"],
        "-hakrawlerproxy",settings["hakrawler_proxy"]
    )
    await proc.wait()

async def remove_url_parameters_combination(output_filename,input_filename):
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["qrreplace_script"],
        "-qreplace",settings["qrreplace_tool"],
        "-program",program_id,
        "-processingfolder",settings["results_folder"],
        "-outputfilename",output_filename,
        "-inputfilename",input_filename
    )
    await proc.wait()

async def paths_from_urls(output_filename,input_filename,unfurl_mode,live_subdomains_file):
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["unfurl_script"],
        "-unfurl",settings["unfurl_tool"],
        "-program",program_id,
        "-processingfolder",settings["results_folder"],
        "-outputfilename",output_filename,
        "-inputfilename",input_filename,
        "-unfurlcommand",unfurl_mode,
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"]

    )
    await proc.wait()     

async def screenshotting():
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["screenshotting_script"],
        "-program",program_id,
        "-processingfolder",settings["results_folder"],
        "-outputfolder","screenshotting-program-"+program_id+"/",
        "-aquatone",settings["aquatone"],
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"]
    )
    await proc.wait()

async def directory_brute_forcing():
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["directory_brute_forcing_script"],
        "-program",program_id,
        "-processingfolder",settings["results_folder"],
        "-outputfolder","directory-brute-forcing-"+program_id+"/",
        "-ffuf",settings["ffuf_tool"],
        "-dbname", settings["dbname"],
        "-dbhost", settings["dbhost"],
        "-dbuser", settings["dbuser"],
        "-dbpass", settings["dbpass"]
    )
    await proc.wait()

async def js_link_finder():
    proc = await asyncio.create_subprocess_exec(
        "python3",settings["js_link_finder_script"],
        "-program",program_id,
        "processingfolder",settings["results_folder"],
        "outputfoldername","js-link-finder-"+program_id+"/"
    )
    await proc.wait()

async def root_domains_from_asns_main():
    # execute root_domains_from_asns.py
    print ("[+] Executing root domains from asns.")
    root_domains_from_asns_task = asyncio.create_task(root_domains_from_asns())
    await asyncio.wait((root_domains_from_asns_task,))
    print("[+] Completed executing root domains from asns. Validating findings with dns.")
    root_domains_from_asns_dns_validation_output_filename=root_domains_from_asns_output_filename.replace(".txt","")+"_dnsValidated.txt"
    root_domains_from_asns_dns_validation_task = asyncio.create_task(validate_with_dns(root_domains_from_asns_output_filename,root_domains_from_asns_dns_validation_output_filename))
    await asyncio.wait((root_domains_from_asns_dns_validation_task,))
    if input("[+] Completed dns validation for subdomains from domains. Sync to server? [Y/N]").lower()=="y":
        print("[+] Syncing to server.")
        await sync_to_server("root_domains_from_asns",settings["results_folder"]+root_domains_from_asns_dns_validation_output_filename)
        print("[+] Syncing completed.")
    print("========================================================================================================================")


async def execute_subdomains_from_domains_main():
    # execute subdomains from domains
    input("[+] Press enter to run subdomains from domains")
    print ("[+] Executing subdomains from domains.")
    subsomains_from_domains_task = asyncio.create_task(subdomains_from_domains())
    await asyncio.wait((subsomains_from_domains_task,))
    print("[+] Completed executing subdomains from domains. Validating findings with dns.")
    sub_domains_from_domains_dns_validation_output_filename = subdomains_from_domains_output_filename.replace(".txt","")+"_dnsValidated.txt"
    sub_domains_from_domains_dns_validation_task = asyncio.create_task(validate_with_dns(subdomains_from_domains_output_filename,sub_domains_from_domains_dns_validation_output_filename))
    await asyncio.wait((sub_domains_from_domains_dns_validation_task,))
    if input("[+] Completed dns validation for subdomains from domains. Sync to server? [Y/N]").lower()=="y":
        print("[+] Syncing to server.")
        await sync_to_server("subdomains_from_domains",settings["results_folder"]+sub_domains_from_domains_dns_validation_output_filename)
        print("[+] Syncing completed.")
    print("========================================================================================================================")

async def subdomains_from_alternative_scans_main():
    # #execute subdomains from alternative scans
    input("[+] Press enter to run subdomains from altdns?")
    print ("[+] Executing subdomains from altdns.")
    subsomains_from_altdns_task = asyncio.create_task(altdns_from_subdomains())
    await asyncio.wait((subsomains_from_altdns_task,))
    print ("[+] Completed executing subdomains from altdns. Validating findings with dns.")
    sub_domains_from_altdns_dns_validation_output_filename = altdns_from_subdomains_output_filename.replace(".txt","")+"_dnsValidated.txt"
    sub_domains_from_altdns_dns_validation_task = asyncio.create_task(validate_with_dns(altdns_from_subdomains_output_filename,sub_domains_from_altdns_dns_validation_output_filename))
    await asyncio.wait((sub_domains_from_altdns_dns_validation_task,))
    if input("[+] Completed dns validateion for subdomains from alternative scans. Sync to server? [Y/N]").lower()=="y":
        print("[+] Syncing to server.")
        await sync_to_server("subdomains_from_altdns",settings["results_folder"]+sub_domains_from_altdns_dns_validation_output_filename)
        print("[+] Syncing completed.")
    print("========================================================================================================================")

async def httprobe_validation_main():
    #execute httprobe validation
    input("[+] Press enter to run httprobe on subdomains")
    print ("[+] Executing httprobe on subdomains.")
    httprobe_on_subdomains_task = asyncio.create_task(httprobe_on_subdomains(httprobe_on_subdomains_output_filename))
    await asyncio.wait((httprobe_on_subdomains_task,))
    if input("[+] Completed httprobe validation for subdomains. Sync to server? [Y/N]").lower()=="y":
        print("[+] Syncing to server.")
        await sync_to_server("subdomains_from_httprobe",settings["results_folder"]+httprobe_on_subdomains_output_filename)
        print("[+] Syncing completed.")
    print("========================================================================================================================")

async def urls_from_subdomain_main():
    #execute URLs from subdomains
    input("[+] Press enter to run urls from subdomains")
    print ("[+] Executing urls from subdomains.")
    urls_from_subdomains_task = asyncio.create_task(urls_from_subdomains(urls_from_subdomains_output_filename))
    await asyncio.wait((urls_from_subdomains_task,))
    remove_duplicate_url_paramaetes_combination_task = asyncio.create_task(remove_url_parameters_combination(urls_from_subdomains_output_filename_duplicates_removed,urls_from_subdomains_output_filename))
    await asyncio.wait((remove_duplicate_url_paramaetes_combination_task,))
    print("========================================================================================================================")

async def paths_from_urls_main(input_file_name):
    input("[+] Press enter to unfurl urls. Make sure to copy the urls from burp, etc.. into the file.")
    #execute paths from urls
    print("[+] Unfurling paths from urls.")
    unfurling_paths_task = asyncio.create_task(paths_from_urls(unfurled_urls_paths_brute_force_output_filename,input_file_name,"paths",httprobe_on_subdomains_output_filename))
    await asyncio.wait((unfurling_paths_task,))
    print("[+] Make sure to append wordlists to the custom generated one based on tech type before bruteforcing.")
    print("========================================================================================================================")
    #add execute querystring keys, values, etc....... IMPORTANT

async def screenshotting_main():
    input("[+] Press enter to screenshot subdomains")
    print("[+] Screenshotting subdomains")
    screenshotting_task = asyncio.create_task(screenshotting())
    await asyncio.wait((screenshotting_task,))
    print("========================================================================================================================")

async def js_link_finder_main():
    input ("[+] Press enter to run js from javascript. Make sure js is extracted from burp per subdomain.")
    print("[+] Running JS Analysis.")
    js_files = asyncio.create_task()

async def main():
    print("[+] Starting Automation...")
    # await root_domains_from_asns_main()
    await execute_subdomains_from_domains_main()
    await subdomains_from_alternative_scans_main()
    # await httprobe_validation_main()
    # #TODO: SYNC THINGS TO SERVER AND LOAD FROM SERVER
    # await urls_from_subdomain_main()
    # await paths_from_urls_main(urls_from_subdomains_output_filename_duplicates_removed)
    # await screenshotting_main()
    # await directory_brute_forcing()
    
    print("========================================================================================================================")

    



if __name__ == "__main__":
    loadSettings()
    setup()
    asyncio.run(main())
    


    
    

