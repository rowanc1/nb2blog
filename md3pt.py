#!/usr/local/bin/python
import requests, argparse, p3c, os, json, subprocess, keyring

host3pt = "http://www.3ptscience.com/api/"

def parseMarkdown(f):

    md = str(f.read())
    f.close()
    inMetaMode = True
    mdNoMeta = []
    meta = dict()

    for line in md.split('\n'):
        if inMetaMode and len(line) == 0:
            continue
        elif inMetaMode and line[0] == ':':
            key_data = line.split(':')
            assert len(key_data) >= 3
            key, data = key_data[1], ':'.join(key_data[2:])
            meta[key] = data.strip()
        else:
            mdNoMeta += [line]
            inMetaMode = False

    return md, "\n".join(mdNoMeta), meta


def main():
    parser = argparse.ArgumentParser(description='Upload a markdown to a gist and 3point/SimPEG blog.')
    parser.add_argument('markdown', type=str, help='The file name of the markdown.')
    args = parser.parse_args()

    # Get the data ready for uploading to gist.github.com
    mdFile = file(args.markdown,'r')
    md, mdNoMeta, meta = parseMarkdown(mdFile)
    assert 'uid' in meta, "Must have a :uid: defined at the beginning of your markdown."
    data =  {
              "description": meta.get('description', ""),
              "public": True,
              "files": {}
            }
    data['files'][args.markdown.split('/')[-1]] = {"content": md}


    token = keyring.get_password('3pt','github.gist')
    if token is None:
        raise Exception("""keyring could not find your gist token:

            ipython
            >  import keyring
            >  keyring.set_password('3pt', 'github.gist', 'YOUR GITHUB TOKEN')

            Go to github to create one if you haven't made it yet (make sure you enable gist,repo,user):

            https://github.com/settings/applications#personal-access-tokens
        """)

    token3pt = keyring.get_password('3pt','3pt')
    if token3pt is None:
        raise Exception("""keyring could not find your 3point token:

            ipython
            >  import keyring
            >  keyring.set_password('3pt', '3pt', 'YOUR 3POINT TOKEN')

            You may need to get one from 3point Science!

        """)

    # Check if the source is in the meta dict, and post to gist.github.com
    if 'source' in meta and ('api.github.com/gists/' in meta['source'] or 'gist.github.com/' in meta['source']):
        gistId = meta['source'].split('/')[-1].strip('.git')
        resp = requests.patch("https://api.github.com/gists/%s?access_token=%s"%(gistId,token), data=json.dumps(data))
    elif 'source' not in meta:
        resp = requests.post("https://api.github.com/gists?access_token=%s"%token, data=json.dumps(data))
        url  = resp.json()['url']
        meta["source"] = url


    data3pt = {
        'content': mdNoMeta,
        'isMarkdown': True,
    }

    for key in ['title', 'description', 'group', 'tag', 'tooltip', 'source', 'license']:
        if meta.get(key, None):
            data3pt[key] = meta[key]

    exists = requests.get(host3pt + 'verify/blog/uid', params={'test':meta["uid"]}).json().get('exists', False)
    if exists:
        resp = requests.post(host3pt + "blog/%s?sshKey=%s&_method=PATCH"%(meta["uid"], token3pt), data=data3pt)
        meta3pt = resp.json()
    else:
        data3pt['uid'] = meta['uid']
        resp = requests.post(host3pt + "blog?sshKey=%s"%token3pt, data=data3pt)
        meta3pt = resp.json()

    f = file(args.markdown,'w')
    for key in ['uid', "title", "description", "tooltip"]:
        f.write(':%s: %s\n'%(key, meta3pt[key]))
    for key in ["tag", "group"]:
        f.write(':%s: %s\n'%(key, ','.join(meta3pt[key])))
    for key in ["license", "source"]:
        f.write(':%s: %s\n'%(key, meta3pt[key]))
    f.write("\n")
    f.write(mdNoMeta)
    f.close()

if __name__ == "__main__":
    main()
