from asyncio.subprocess import PIPE
import datetime
from xmlrpc.client import DateTime
import mysql.connector
import argparse
import os
import asyncio

program_id=""
operation=""
input_file=""
db_name=""
db_host=""
db_pass=""
db_user=""
aws_access_key=""
aws_secret_key=""
bucket_name=""

def setup():
    global program_id,operation,input_file,db_host,db_name,db_pass,db_user,aws_access_key,aws_secret_key,bucket_name

    par = argparse.ArgumentParser()
    par.add_argument('-programid')
    par.add_argument('-operation')
    par.add_argument('-inputfile')
    par.add_argument('-dbname')
    par.add_argument('-dbhost')
    par.add_argument('-dbuser')
    par.add_argument('-dbpass')
    par.add_argument('-awsaccesskey')
    par.add_argument('-awssecretkey')
    par.add_argument('-bucketname')

    args = par.parse_args()
    program_id= args.programid
    operation  = args.operation
    input_file = args.inputfile
    db_name = args.dbname
    db_host = args.dbhost
    db_pass = args.dbpass
    db_user = args.dbuser
    aws_access_key = args.awsaccesskey
    aws_secret_key = args.awssecretkey
    bucket_name = args.bucketname

def root_domains_from_asns():
    domains=[]
    to_insert=[]
    with open(input_file,'r') as input:
        domains = input.readlines()
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    for domain in domains:
        to_insert.append((program_id,domain.replace("\n",""),datetime.datetime.now(),datetime.datetime.now(),"N/A",datetime.datetime.now()))
    cur = db.cursor()
    #there is also insert ignore
    sql = "insert into domains (program_id,domain,created,modified,is_live) values (%s,%s,%s,%s,%s) on duplicate key update modified=%s" 
    cur.executemany(sql,to_insert)
    db.commit()
    cur.close()
    db.close()

def subdomains_from_domains():
    #we will check line by line, if it is a domain we will add it to the domains list for db
    #if it is a subdomain it will go through the subdomain routine
    subdomains = []
    to_insert_subdomains=[]
    to_insert_domains=[]
    with open(input_file,'r') as input:
        subdomains = input.readlines()
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    for subdomain in subdomains:
        if subdomain.count('.')>1: #subdomain       
            split= subdomain.split('.')
            domain = split[len(split)-2]+"."+split[len(split)-1]
            to_insert_subdomains.append((domain.replace("\n",""),subdomain.replace("\n",""),program_id,datetime.datetime.now(),datetime.datetime.now(),"N/A",datetime.datetime.now()))
        elif subdomain.count('.')==1: #domain
            to_insert_domains.append((program_id,subdomain.replace("\n",""),datetime.datetime.now(),datetime.datetime.now(),"N/A",datetime.datetime.now()))
    sql_domain = "insert into domains (program_id,domain,created,modified,is_live) values (%s,%s,%s,%s,%s) on duplicate key update modified=%s" 
    sql_subdomain = "insert ignore into subdomains (domain,subdomain,program_id,created,modified,is_live) values (%s,%s,%s,%s,%s,%s) on duplicate key update modified=%s"
    cur = db.cursor()
    if len(to_insert_domains)>0:
        cur.executemany(sql_domain,to_insert_domains)
    if len(sql_subdomain)>0:
        cur.executemany(sql_subdomain,to_insert_subdomains)
    db.commit()
    cur.close()
    db.close()   

def subdomains_from_altdns():
    to_insert=[]
    with open(input_file,'r') as input:
        subdomains = input.readlines()
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    for subdomain in subdomains:
        split= subdomain.split('.')
        domain = split[len(split)-2]+"."+split[len(split)-1]
        to_insert.append((domain,subdomain.replace("\n",""),program_id,datetime.datetime.now(),datetime.datetime.now(),datetime.datetime.now()))
    
    cur = db.cursor()
    sql_subdomain = "insert ignore into subdomains (domain,subdomain,program_id,created,modified) values (%s,%s,%s,%s,%s) on duplicate key update modified=%s"
    if len(to_insert)>0:
        cur.executemany(sql_subdomain,to_insert)
    db.commit()
    cur.close()
    db.close()

def subdomains_from_httprobe():
    to_insert_http=[]
    to_insert_https=[]
    with open(input_file,'r') as input:
        subdomains = input.readlines()
    db = mysql.connector.connect(
        host=db_host,
        user=db_user,
        passwd=db_pass,
        database = db_name
    )
    for subdomain in subdomains:
        split= subdomain.split('.')
        domain = split[len(split)-2]+"."+split[len(split)-1]
        if("https" in subdomain):
            to_insert_https.append((domain.replace("\n","").replace("http://","").replace("https://",""),subdomain.replace("\n","").replace("http://","").replace("https://",""),program_id,datetime.datetime.now(),"yes","yes",datetime.datetime.now(),"yes"))
        else: #means it is http
            to_insert_http.append((domain.replace("\n","").replace("http://","").replace("https://",""),subdomain.replace("\n","").replace("http://","").replace("https://",""),program_id,datetime.datetime.now(),"yes","yes",datetime.datetime.now(),"yes"))

    sql_subdomain_http = "insert ignore into subdomains (domain,subdomain,program_id,modified,is_live,is_https_live) values (%s,%s,%s,%s,%s,%s) on duplicate key update modified=%s,is_live=%s"
    sql_subdomain_https = "insert ignore into subdomains (domain,subdomain,program_id,modified,is_live,is_https_live) values (%s,%s,%s,%s,%s,%s) on duplicate key update modified=%s,is_https_live=%s"
    cur = db.cursor()
    if len(to_insert_http)>0:
        cur.executemany(sql_subdomain_http,to_insert_http)
    if len(to_insert_https)>0:
        cur.executemany(sql_subdomain_https,to_insert_https)
    db.commit()
    cur.close()
    db.close()   

async def subdomain_takeover():
    await upload_s3_file(input_file,bucket_name+"/"+program_id+"/subdomain_takover/","subdomain_takeover.txt")

async def upload_s3_file(file,foldername,filename):
    # session = boto3.Session(
    #     aws_access_key_id=aws_access_key,
    #     aws_secret_access_key=aws_secret_key,
    # )
    # s3_client = session.resource('s3')
    # with open(file,'rb') as f:
    #     s3_client.upload_fileobj(f,"Bugbounty/"+program_id+"/"+foldername,filename)
    proc = await asyncio.create_subprocess_shell("aws s3 cp "+file+" s3://"+foldername+filename,stdout=PIPE)
    await proc.wait()

def rename_file():
    os.rename(os.path.abspath(input_file),os.path.abspath(input_file)+".SYNCED")

async def main():
    if operation.lower()=="root_domains_from_asns":
        root_domains_from_asns()
        rename_file()
    elif operation.lower()=="subdomains_from_domains":
        subdomains_from_domains()
        rename_file()
    elif operation.lower()=="subdomains_from_altdns":
        subdomains_from_altdns()
        rename_file()
    elif operation.lower()=="subdomains_from_httprobe":
        subdomains_from_httprobe()
        rename_file()
    elif operation.lower()=="subdomain_takeover":
        await subdomain_takeover()
        rename_file


if __name__ == "__main__":
    setup()
    asyncio.run(main())





