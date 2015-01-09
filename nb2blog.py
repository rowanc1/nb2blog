#!/usr/local/bin/python
import requests, argparse, p3c, os, json, subprocess, keyring

p3c.Comms.host = 'local'


def main():
    parser = argparse.ArgumentParser(description='Upload a notebook to a gist and 3point/SimPEG blog.')
    parser.add_argument('notebook', type=str, help='The file name of the notebook.')
    parser.add_argument('-m', type=str, help='Description of the notebook.')
    args = parser.parse_args()

    jsonFile = '/'.join(p3c.__file__.split('/')[:-1]+['nb2blog.json'])
    if os.path.exists(jsonFile):
        with file(jsonFile,'r') as f:
            R = json.loads(f.read())
    else:
        f = file(jsonFile,'w')
        f.write('{}\n')
        f.close()
        R = {}

    # Get the data ready for uploading to gist.github.com
    ipynb = file(args.notebook,'r')
    data =  {
              "description": args.m,
              "public": True,
              "files": {}
            }
    data['files'][args.notebook] = {"content": str(ipynb.read())}
    ipynb.close()

    token = keyring.get_password('3pt','github.gist')
    if token is None:
        raise Exception("""keyring could not find your gist token:

            ipython
            >  import keyring
            >  keyring.set_password('3pt', 'github.gist', 'YOUR GITHUB TOKEN')

            Go to github to create one if you haven't made it yet (make sure you enable gist,repo,user):

            https://github.com/settings/applications#personal-access-tokens
        """)

    # Check if the ipynb is in the dict, and post to gist.github.com
    if args.notebook in R:
        url = R[args.notebook]['gistURL']
        resp = requests.patch("%s?access_token=%s"%(url,token), data=json.dumps(data))
    else:
        resp = requests.post("https://api.github.com/gists?access_token=%s"%token, data=json.dumps(data))
        url  = resp.json()['url']
        R[args.notebook] = {"gistURL": url}

    gitResp = resp.json()

    f = file(jsonFile,'w')
    f.write(json.dumps(R))
    f.close()

    # Convert the notebook to html
    subprocess.check_output("ipython nbconvert %s --to html --template basic" % (args.notebook.replace(' ','\\ ')), shell=True)
    f = file(args.notebook.replace('ipynb','html'),'r')
    nbhtml = f.read()
    f.close()
    subprocess.check_output("rm %s" % (args.notebook.replace(' ','\\ ')).replace('ipynb','html'), shell=True)


    uid = args.notebook[:-6].lower().replace(' ','-')
    title = args.notebook[:-6].title()
    b = p3c.Blog.new({'uid':uid,"content":nbhtml, "title":title, "description": args.m, 'setTags':'simpeg'})


if __name__ == "__main__":
    main()
