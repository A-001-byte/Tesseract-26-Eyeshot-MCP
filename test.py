import urllib.request, json
url = 'http://localhost:8000/api/v1/tools/chat'

prompts = [
    'load the bracket assembly',
    'make the bracket assembly taller by 50 mm',
    'scale the bracket assembly by 0.5',
    'load the gear plate',
    'put together an assembly of all parts'
]

for p in prompts:
    print(f'>>> Testing: {p}')
    try:
        data = json.dumps({'prompt': p}).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            print(f"SUCCESS! Name: {res.get('name')} | Volume: {res.get('volume_m3', 0):.4f}")
    except Exception as e:
        print(f'ERROR: {e}')
        if hasattr(e, 'read'):
            print(e.read().decode())
