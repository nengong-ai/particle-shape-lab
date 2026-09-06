#!/usr/bin/env python3
"""Bridge shape data to a separately supplied runtime; no engine is distributed here."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import xml.etree.ElementTree as ET
from svg_input import parse_svg

PUBLIC_ROOT=Path(__file__).resolve().parents[1]


def validate_shape(path):
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    if payload.get('schemaVersion')!=1:raise ValueError('Unsupported shape schema.')
    g=payload['geometry']
    allowed={'width','height','viewBox','paths','fillRules','filled','label'}
    if set(g)-allowed:raise ValueError('Unexpected geometry keys; no motion presets or executable payloads are accepted.')
    label=g.get('label','Untitled')
    if not isinstance(label,str) or not label.strip() or len(label)>120 or any(ord(c)<32 for c in label):raise ValueError('Invalid label.')
    if not isinstance(g.get('paths'),list) or not isinstance(g.get('fillRules'),list) or len(g['paths'])!=len(g['fillRules']):raise ValueError('Paths and fillRules must have equal length.')
    svg=ET.Element('svg',{'viewBox':g['viewBox'],'fill':'white'})
    for d,rule in zip(g['paths'],g['fillRules']):ET.SubElement(svg,'path',{'d':d,'fill-rule':rule})
    geometry,normalized=parse_svg(ET.tostring(svg,encoding='utf-8'))
    geometry.update(filled=True,label=label)
    return {'schemaVersion':1,'geometry':geometry},normalized


def runtime_files(source,contracts):
    if source.is_symlink() or not source.is_dir():raise ValueError('Runtime must be a local regular directory.')
    errors=[]
    for name,contract in contracts['contracts'].items():
        files={}
        try:
            for relative,sha in contract['files'].items():
                p=PurePosixPath(relative)
                if p.is_absolute() or any(x in ('','..','.') for x in relative.split('/')) or '\\' in relative:raise ValueError('Unsafe contract path.')
                path=source/relative
                if any(q.is_symlink() for q in [path,*list(path.parents)[:len(p.parts)-1]]):raise ValueError('Runtime symlink is not allowed: '+relative)
                data=path.read_bytes()
                if hashlib.sha256(data).hexdigest()!=sha:raise ValueError('Runtime differs: '+relative)
                files[relative]=data
            return name,files
        except (ValueError,OSError) as error:errors.append(name+': '+str(error))
    raise ValueError('No compatible runtime matched. '+ '; '.join(errors))


def export_project(runtime,shape_path,destination,contracts=None):
    raw_runtime=Path(runtime).absolute()
    if any(p.is_symlink() for p in [raw_runtime,*raw_runtime.parents]):raise ValueError('Runtime path cannot use symlinks.')
    runtime=raw_runtime.resolve();raw_dest=Path(destination).absolute()
    if any(p.is_symlink() for p in [raw_dest,*raw_dest.parents]):raise ValueError('Destination path cannot use symlinks.')
    destination=raw_dest.resolve()
    for protected in [runtime,PUBLIC_ROOT]:
        if destination==protected or protected in destination.parents or destination in protected.parents:raise ValueError('Destination must be outside runtime and tool repository.')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):raise ValueError('Destination must be new or empty.')
    payload,normalized=validate_shape(shape_path)
    if contracts is None:contracts=json.loads((PUBLIC_ROOT/'scripts/runtime-contracts.json').read_text(encoding='utf-8'))
    name,vendor=runtime_files(runtime,contracts)
    files={}
    for path,data in vendor.items():
        if path.startswith('src/'):
            files[path]=data
        else:files['runtime-notices/'+path]=data
    files['src/main.ts']=(PUBLIC_ROOT/'scripts/adapter.ts').read_bytes()
    files['src/screen.css']=(PUBLIC_ROOT/'scripts/screen.css').read_bytes()
    files['input/shape.json']=(json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
    files['input/normalized.svg']=normalized
    originals_preserved = False
    origin_folder = Path(shape_path).absolute().parent
    origin_manifest = origin_folder / 'manifest.json'
    if origin_manifest.exists():
        if origin_manifest.is_symlink(): raise ValueError('Input manifest cannot be a symlink.')
        origin = json.loads(origin_manifest.read_text(encoding='utf-8'))
        kind = origin.get('inputType')
        if kind not in ('svg', 'png'): raise ValueError('Invalid original input type in manifest.')
        original = origin_folder / ('original.' + kind)
        if original.is_symlink(): raise ValueError('Original input cannot be a symlink.')
        original_bytes = original.read_bytes()
        if hashlib.sha256(original_bytes).hexdigest() != origin.get('inputSha256'):
            raise ValueError('Original input hash differs from its manifest.')
        files['input/original.' + kind] = original_bytes
        files['input/manifest.json'] = origin_manifest.read_bytes()
        originals_preserved = True
    for path in ['package.json','package-lock.json']:
        files[path]=(PUBLIC_ROOT/path).read_bytes()
    package=json.loads(files['package.json']);package['name']='local-particle-export';package.pop('license',None)
    package['scripts']={'check':'node build.mjs --check','build':'node build.mjs'}
    files['package.json']=(json.dumps(package,indent=2)+'\n').encode()
    lock=json.loads(files['package-lock.json'])
    lock['name']=package['name']
    if '' in lock.get('packages',{}):
        lock['packages']['']['name']=package['name']
        lock['packages'][''].pop('license',None)
    files['package-lock.json']=(json.dumps(lock,indent=2)+'\n').encode()
    for path in ['build.mjs','serve.py']:files[path]=(PUBLIC_ROOT/'scripts'/path).read_bytes()
    files['tsconfig.json']=json.dumps({'compilerOptions':{'target':'ES2022','lib':['ES2022','DOM','DOM.Iterable'],'module':'ESNext','moduleResolution':'Bundler','jsx':'react-jsx','resolveJsonModule':True,'isolatedModules':True,'verbatimModuleSyntax':True,'strict':True,'skipLibCheck':True,'noEmit':True,'types':['vite/client','node']},'include':['src/**/*.ts','src/**/*.tsx']},indent=2).encode()
    files['vite.config.ts']=b'import { defineConfig } from "vite";\nexport default defineConfig({ cacheDir: ".tmp/vite", server: { host: "127.0.0.1" } });\n'
    title=html.escape(payload['geometry']['label'])
    files['index.html']=f'<!doctype html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><link rel="icon" href="/icon.svg"></head><body><div id="root"></div><script type="module" src="/src/main.ts"></script></body></html>\n'.encode()
    files['public/icon.svg']=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path fill="white" d="M10 1 19 10 10 19 1 10Z"/></svg>\n'
    report={'originalInputPreserved':originals_preserved,'runtimeContract':name,'runtimeFiles':{p:hashlib.sha256(b).hexdigest() for p,b in vendor.items()},'shapeSha256':hashlib.sha256(files['input/shape.json']).hexdigest(),'browserVerified':False,'dependencies':'not installed; run npm ci','licenseScope':'Tool MIT does not license supplied runtime or user input.'}
    files['export.json']=(json.dumps(report,indent=2)+'\n').encode()
    files['README.md']=b'# Local particle export\n\nRun `npm ci`, `node build.mjs --check`, `node build.mjs`, then `python3 serve.py --port 4195`. Node22.13+ and an HTTP/WebGL browser are required. This export does not use any old node_modules link.\n\nThe engine was supplied separately by the caller; its copied files retain their original license status. See runtime-notices/ and src/particles/core/README.md. The input tool MIT license does not relicense that engine, its assets or user input. Do not publish this output based only on the tool license. The adapter does not provide the private brand presets or renderer patches.\n\nCapture actual browser acceptance separately; export.json keeps browserVerified:false because writing files is not a rendering test.\n'
    destination.parent.mkdir(parents=True,exist_ok=True);staging=Path(tempfile.mkdtemp(prefix='.particle-export-',dir=destination.parent))
    try:
        for relative,data in files.items():
            p=staging/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        if destination.exists():destination.rmdir()
        os.rename(staging,destination)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',required=True,type=Path);p.add_argument('--shape',required=True,type=Path);p.add_argument('--dest',required=True,type=Path);a=p.parse_args()
    try:r=export_project(a.runtime,a.shape,a.dest)
    except (ValueError,OSError,KeyError,TypeError,ET.ParseError) as e:p.error(str(e))
    print(json.dumps({'created':str(a.dest.resolve()),'runtimeContract':r['runtimeContract'],'browserVerified':False},ensure_ascii=False))
if __name__=='__main__':main()
