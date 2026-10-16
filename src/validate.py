"""Basic PDF preflight: pages, searchable text, clipping, photo and file health."""
import argparse,json,sys,fitz
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('files',nargs='+');a=p.parse_args();fail=False
for path in a.files:
    doc=fitz.open(path);issues=[]
    if len(doc)>2:issues.append(f'page count {len(doc)} exceeds 2')
    if len(doc)<1:issues.append('empty PDF')
    for n,page in enumerate(doc,1):
        if len(page.get_text().strip())<100:issues.append(f'page {n} not searchable')
        for b in page.get_text('blocks'):
            if b[6]==0 and (b[0]<-1 or b[1]<-1 or b[2]>page.rect.width+1 or b[3]>page.rect.height+1):issues.append(f'page {n} text out of bounds')
    if not doc[0].get_images():issues.append('original photo missing')
    result={'file':path,'pages':len(doc),'status':'FAIL' if issues else 'PASS','issues':issues}
    print(json.dumps(result,ensure_ascii=False));fail|=bool(issues)
sys.exit(1 if fail else 0)
