#!/usr/bin/env python3
"""Normalize a simple SVG/PNG into renderer-neutral shape data."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET
from svg_input import parse_svg


def convert(source, destination, title=None, foreground='auto', threshold=128):
    source=Path(source).resolve(); raw_destination=Path(destination).absolute()
    if any(p.is_symlink() for p in [raw_destination,*raw_destination.parents]):
        raise ValueError('Output path must not use symlinks.')
    destination=raw_destination.resolve()
    if destination==source or destination in source.parents:
        raise ValueError('Output must not contain the input file.')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError('Output must be new or empty.')
    title=title or source.stem
    if not title.strip() or len(title)>120 or any(ord(c)<32 for c in title):
        raise ValueError('Title needs 1–120 visible characters.')
    raw=source.read_bytes(); kind=source.suffix.lower()
    trace=None
    if kind=='.png':
        from png_input import trace_png
        intermediate,trace=trace_png(source,foreground,threshold)
        geometry,normalized=parse_svg(intermediate)
    elif kind=='.svg':
        geometry,normalized=parse_svg(raw);intermediate=None
    else:raise ValueError('Input must be a static .svg or .png file.')
    geometry.update({'filled':True,'label':title})
    payload={'schemaVersion':1,'geometry':geometry}
    manifest={'inputType':kind[1:],'inputSha256':hashlib.sha256(raw).hexdigest(),
              'normalizedSha256':hashlib.sha256(normalized).hexdigest(),'trace':trace,
              'normalization':'SVG coordinates/viewBox retained; PNG is thresholded and cropped to its foreground bounds.',
              'browserVerified':False}
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.shape-',dir=destination.parent))
    try:
        (staging/('original'+kind)).write_bytes(raw)
        (staging/'normalized.svg').write_bytes(normalized)
        if intermediate:(staging/'traced.svg').write_bytes(intermediate)
        (staging/'shape.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        (staging/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if destination.exists():destination.rmdir()
        os.rename(staging,destination)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    p.add_argument('--title');p.add_argument('--foreground',choices=['auto','alpha','dark','light'],default='auto')
    p.add_argument('--threshold',type=int,default=128);a=p.parse_args()
    try:r=convert(a.input,a.out,a.title,a.foreground,a.threshold)
    except (ValueError,OSError,ET.ParseError) as e:p.error(str(e))
    print(json.dumps({'created':str(a.out.resolve()),'inputType':r['inputType'],'browserVerified':False},ensure_ascii=False))
if __name__=='__main__':main()
