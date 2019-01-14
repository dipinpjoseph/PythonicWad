import sys
import requests
from ifsc_excel_reader import ifsc_excel_reader
import time

access_token = "Bearer "+sys.argv[1:][0]
blog_id = "" #Your Blog Id here
blogger_url = "https://www.googleapis.com/blogger/v3/blogs/"+str(blog_id)+"/posts/"

branch_list = ifsc_excel_reader()
template = open("html_template.txt", "r").read()
for each_post in branch_list:
    ifsc_checker = open("ifsc_check.txt", "r").read()
    if each_post['IFSC Code'] in ifsc_checker:
        print("Already published"+each_post['IFSC Code'])
        continue
    post_title = "IFSC Code of "+each_post['Bank Branch']+" "+ each_post['Bank Name']
    labels = []
    labels.append(each_post['Bank Name'])
    labels.append(each_post['Bank Branch'])
    labels.append(each_post['City'])
    labels.append("IFSC Codes - INDIA")
    template_updated = template
    for key, value in each_post.items():
        key_braces = '{{'+key+'}}'
        template_updated = template_updated.replace(key_braces,value)

    post_data = {"kind": "blogger#post","blog": {"id": str(blog_id) },"title": post_title, "content": template_updated.replace("\n",""), "labels" : labels}
    headers = {'content-type': 'application/json','Authorization':access_token}

    res = requests.post(blogger_url, json=post_data, headers=headers)
    print(res)
    if(res.status_code != 200):
        break
    open("ifsc_check.txt","a+").write(each_post['IFSC Code'])
