"""Resume System: immutable original photo; external JSON; 2-page ReportLab rendering."""
import argparse, json, os, sys, hashlib, datetime, shutil
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
SECTION_TOP_GAP=21
SECTION_RULE_GAP=8
SECTION_CONTENT_GAP=8
FIRST_BASELINE_OFFSET=16
PARAGRAPH_TOP_ADJUST=12
W,H=A4; LEFT=39; RIGHT=W-39; WIDTH=RIGHT-LEFT; TOP=H-39; BOTTOM=39
INK=HexColor('#171717'); MUTED=HexColor('#666666'); RULE=HexColor('#303030')

def load_json(p):
    with open(p,encoding='utf-8') as f:return json.load(f)

def fonts():
    """Use locally installed Pretendard if provided; never package or redistribute font files."""
    search=[Path(os.environ.get('PRETENDARD_DIR','/mnt/data')),Path('/mnt/data'),Path.home()/'.local/share/fonts',Path('/usr/share/fonts/truetype')]
    def find(names):
        for d in search:
            if d.exists():
                for n in names:
                    m=list(d.rglob(n))
                    if m:return m[0]
        return None
    reg=find(['Pretendard-Regular.ttf','PretendardVariable.ttf'])
    bold=find(['Pretendard-Bold.ttf','Pretendard-SemiBold.ttf'])
    if reg and bold:
        try:
            pdfmetrics.registerFont(TTFont('Body',str(reg)))
            pdfmetrics.registerFont(TTFont('Bold',str(bold)))
            return 'Pretendard'
        except Exception as e:print('Pretendard font loading failed:',e,file=sys.stderr)
    reg=Path('/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf')
    bold=Path('/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf')
    if not reg.exists():raise RuntimeError('Pretendard 또는 NanumBarunGothic TTF 설치 필요')
    pdfmetrics.registerFont(TTFont('Body',str(reg)));pdfmetrics.registerFont(TTFont('Bold',str(bold)))
    return 'NanumBarunGothic (Pretendard 대체)'

def text(c,x,y,value,size=9,bold=False,color=INK):
    c.setFillColor(color);c.setFont('Bold' if bold else 'Body',size);c.drawString(x,y,str(value))

def right_text(c,x,y,value,size=8.3,color=MUTED):
    c.setFillColor(color);c.setFont('Body',size);c.drawRightString(x,y,str(value))

def rule(c,y,x=LEFT,width=WIDTH,weight=.85):
    c.setStrokeColor(RULE);c.setLineWidth(weight);c.line(x,y,x+width,y)

def para(c,x,y,value,width=WIDTH,size=10,leading=13,bold=False,color=INK):
    style=ParagraphStyle('body',fontName='Bold' if bold else 'Body',fontSize=size,leading=leading,textColor=color,spaceBefore=0,spaceAfter=0,allowWidows=0,allowOrphans=0,wordWrap='LTR',splitLongWords=0)
    p=Paragraph(escape(str(value)),style)
    w,h=p.wrap(width,1000)
    p.drawOn(c,x,y-h)
    return y-h

def section(c,y,label):
    y-=SECTION_TOP_GAP
    text(c,LEFT,y,label,15,True)
    rule(c,y-SECTION_RULE_GAP)
    return y-SECTION_RULE_GAP-FIRST_BASELINE_OFFSET

def first_para(c,x,baseline,value,width,size=11,leading=15,bold=False,color=INK):
    return para(c,x,baseline+PARAGRAPH_TOP_ADJUST,value,width,size,leading,bold,color)

def bullet(c,y,s,indent=9,size=11.8,leading=15.5):
    text(c,LEFT+indent,y-12,'•',11.0)
    return para(c,LEFT+indent+13,y,s,WIDTH-indent-16,size,leading)-3

def project(c,y,p,compact=False):
    title=p['title']; period=p.get('period','')
    y-=14
    text(c,LEFT+8,y,title,13.2,True)
    right_text(c,RIGHT-3,y,period,11.0)
    y-=14
    if not compact:
        for b in p['bullets']:y=bullet(c,y,b)
    else:
        y=bullet(c,y,p['bullets'][0],size=10.3,leading=14.0)
    return y-19

def footer(c,page):
    right_text(c,RIGHT,H-63,'email: '+person['email'],11.7)
    right_text(c,RIGHT,23,f'page {page}/2',11.0)

def start(c,profile,page):
    text(c,LEFT,H-53,person['name'],22,True)
    text(c,LEFT,H-74,profile['role_title'],11.2)
    rule(c,H-84,weight=1.3)
    footer(c,page)
    return H-101

def contact_and_summary(c,y,profile):
    y=section(c,y,'기본정보')
    photo=next(iter(sorted((ROOT/'assets').glob('profile_original.*'))), None) or next(iter(sorted((ROOT/'assets').glob('profile_sample.*'))), None)
    if photo is None: raise FileNotFoundError('assets/profile_original.* 또는 assets/profile_sample.* 이미지 필요')
    ir=ImageReader(str(photo)); iw,ih=ir.getSize(); pw=91; ph=pw*ih/iw
    py=y-ph+8
    c.drawImage(str(photo),LEFT+8,py,width=pw,height=ph,preserveAspectRatio=True,anchor='c')
    x=LEFT+118
    text(c,x,y-1,'이름  |  '+person['name']+', '+person['english_name'],11.7,True)
    text(c,x,y-17,'연락처  |  '+person['phone'],11.5)
    text(c,x,y-34,'이메일  |  '+person['email'],11.5)
    sy=y-53
    for line in profile['summary']:
        style=ParagraphStyle('sum',fontName='Body',fontSize=11.1,leading=15.0,wordWrap='LTR',splitLongWords=0)
        p=Paragraph('•  '+escape(line),style);_,hh=p.wrap(RIGHT-x-2,1000);p.drawOn(c,x,sy-hh);sy-=hh+1
    return min(py,sy)-7

def education_skills(c,y,data,profile):
    y=section(c,y,'기술 스택')
    labels={'languages':'Language','frameworks':'Framework','automotive':'Automotive','tools':'Tool'}
    for k in profile.get('skills_order',list(data['skills'])):
        text(c,LEFT+8,y,labels.get(k,k),11.9,True)
        y=para(c,LEFT+8,y-8,data['skills'][k],WIDTH-16,11.4,15.3)-16
    y=section(c,y,'학력 및 자격증')
    e=data['education'][0]
    text(c,LEFT+8,y,e['school']+'  |  '+e['major']+' · '+e['degree'],11.8,True)
    right_text(c,RIGHT-3,y,e['period'],10.9)
    y-=26
    for cert in data['certifications']:
        text(c,LEFT+8,y,cert,11.3)
        y-=23
    return y-5

def awards(c,y,data):
    y=section(c,y,'수상 내역')
    for a in data['awards']:
        text(c,LEFT+8,y,a['title'],11.3,True)
        right_text(c,RIGHT-3,y,a['date'],9.4)
        y=para(c,LEFT+8,y-18,a['detail'],WIDTH-18,10.5,14.0)-17
    return y

def work_header(c,y,data):
    y=section(c,y,'직장 경력')
    e=data['experience']
    text(c,LEFT+8,y,e['company'],13.2,True)
    right_text(c,RIGHT-3,y,e['period'],11.0)
    text(c,LEFT+8,y-24,e['team']+'  |  '+e['title'],11.5,color=MUTED)
    return y-43

def project_height(p,compact=False):
    items=p['bullets'][:1] if compact else p['bullets']
    style=ParagraphStyle('measure',fontName='Body',fontSize=11.8,leading=15.5,wordWrap='LTR',splitLongWords=0)
    total=14+14+19
    for item in items:
        _,h=Paragraph(escape(item),style).wrap(WIDTH-25,1000)
        total+=h+3
    return total+12

def compact_skills(c,y,data,profile):
    y=section(c,y,'기술 스택')
    labels={'languages':'Language','frameworks':'Framework','automotive':'Automotive','tools':'Tool'}
    keys=profile.get('skills_order',list(data['skills']))
    starts=[LEFT+8,LEFT+WIDTH/2+4];colw=WIDTH/2-20;heights=[]
    for col in range(2):
        yy=y
        for key in keys[col*2:col*2+2]:
            text(c,starts[col],yy,labels.get(key,key),11.4,True)
            yy=para(c,starts[col],yy-7,data['skills'][key],colw,11,13.5)-12
        heights.append(yy)
    return min(heights)-1

def project_block(c,y,p,academic=False,first=False):
    if not first:
        y-=11
    x=LEFT+8
    title=p['title']; fs=12.4
    text(c,x,y,title,fs,True)
    if not academic:
        label=person.get('company_label','재직 중'); label_x=x+pdfmetrics.stringWidth(title,'Bold',fs)+9
        if label_x+pdfmetrics.stringWidth(label,'Body',9.7)<RIGHT-92:
            text(c,label_x,y,label,9.7,color=MUTED)
    right_text(c,RIGHT-3,y,p.get('period',''),10.5)
    y-=19
    if p.get('contribution'):
        text(c,LEFT+8,y,p['contribution'],10.3,color=MUTED)
        y-=11
    else:
        y+=6
    for item in p['bullets']:
        y=bullet(c,y,item,size=11,leading=18.2)
    return y-16

def project_block_height(p):
    style=ParagraphStyle('estimate',fontName='Body',fontSize=11,leading=18.2,wordWrap='LTR',splitLongWords=0)
    h=39+(16 if p.get('contribution') else 0)
    for b in p['bullets']:
        _,bh=Paragraph(escape(b),style).wrap(WIDTH-25,1000)
        h+=bh+3
    return h

def small_awards(c,y,data):
    y=section(c,y,'수상 내역')
    colw=(WIDTH-26)/2
    lows=[]
    for i,a in enumerate(data['awards']):
        x=LEFT+8+i*(colw+13)
        yy=first_para(c,x,y,a['title'],colw,11.2,14.0,True)
        yy=para(c,x,yy-7,a['organizer']+'  |  '+a['date'],colw,10.5,13.2,color=MUTED)
        yy=para(c,x,yy-7,a['detail'],colw,11,16.0)
        lows.append(yy)
    return min(lows)-12 if lows else y

def education_compact(c,y,data):
    y=section(c,y,'학력 및 자격증')
    e=data['education'][0]
    text(c,LEFT+8,y,e['school']+' · '+e['major']+' ('+e['degree']+')',11.5,True)
    right_text(c,RIGHT-3,y,e['period'],10.5)
    y-=22
    text(c,LEFT+8,y,'GPA '+e['gpa'],10.8,color=MUTED)
    y-=23
    for cert in data['certifications']:
        text(c,LEFT+8,y,cert,11)
        y-=23
    return y-5

def combined_credentials_awards(c,y,data):
    x1=LEFT+8; x2=LEFT+WIDTH/2+9; cw=WIDTH/2-22
    y-=SECTION_TOP_GAP
    text(c,LEFT,y,'학력 및 자격증',15,True)
    text(c,x2,y,'수상 내역',15,True)
    rule(c,y-SECTION_RULE_GAP,x=LEFT,width=cw+5)
    rule(c,y-SECTION_RULE_GAP,x=x2,width=cw)
    yy=y-SECTION_RULE_GAP-FIRST_BASELINE_OFFSET
    e=data['education'][0]
    yy=first_para(c,x1,yy,e['school']+' · '+e['major']+' ('+e['degree']+')',cw,11,15.0,True)-3
    yy=para(c,x1,yy,'GPA '+e['gpa'],cw,10.8,15.0,color=MUTED)-5
    for cert in data['certifications']:
        yy=para(c,x1,yy,cert,cw,11,15.0)-5
    zz=y-SECTION_RULE_GAP-FIRST_BASELINE_OFFSET
    for a in data['awards']:
        zz=first_para(c,x2,zz,a['title'],cw,10.8,14.0,True)-2 if a is data['awards'][0] else para(c,x2,zz,a['title'],cw,10.8,14.0,True)-2
        zz=para(c,x2,zz,a['organizer']+' | '+a['date'],cw,10.1,13.0,color=MUTED)-5
        zz=para(c,x2,zz,a['detail'],cw,10.5,14.0)-7
    return min(yy,zz)-8

def academic_section(c,y,academic):
    if not academic:return y
    y=section(c,y,'학부 개발 프로젝트')
    for p in academic:
        text(c,LEFT+8,y,p['title'],11.5,True)
        right_text(c,RIGHT-3,y,p.get('period',''),10.4)
        y-=11
        for b in p['bullets']:
            y=bullet(c,y,b,size=10.3,leading=18.0)
        y-=14
    return y

def build(data,profile,out,font_used):
    global person
    person=data['person']
    projects={p['id']:p for p in data['projects']}
    ids=profile['primary_project_ids']+profile.get('secondary_project_ids',[])
    practical=[projects[k] for k in ids if 'academic' not in projects[k].get('tags',[])]
    academic=[projects[k] for k in ids if 'academic' in projects[k].get('tags',[])]
    c=canvas.Canvas(str(out),pagesize=A4,pageCompression=1)
    c.setTitle('이력서 - '+person['name']+' - '+profile['role_title'])
    c.setAuthor(person['name'])
    page=1;y=start(c,profile,page)
    def nextpage():
        nonlocal page,y
        if page>=2:raise RuntimeError('2페이지 초과: 내용을 삭제하지 말고 레이아웃을 검토하세요')
        c.showPage();page+=1;y=start(c,profile,page)+10
    def ensure(h):
        if y-h<BOTTOM+12:nextpage()
    y=contact_and_summary(c,y,profile)
    y=compact_skills(c,y,data,profile)
    ensure(110);y=section(c,y,'경력')
    e=data['experience']
    text(c,LEFT+8,y,e['company'],12.4,True)
    right_text(c,RIGHT-3,y,e['period'],10.7)
    text(c,LEFT+8,y-21,e['team']+'  |  '+e['title'],11,color=MUTED)
    y-=38
    resp=e['responsibility']
    if profile['name']=='developer':
        resp=profile.get('responsibility_override',resp)
    y=para(c,LEFT+8,y,resp,WIDTH-16,11,16.0)-12
    ensure(55);y=section(c,y,'프로젝트')
    for i,p in enumerate(practical):
        ensure(project_block_height(p)+15)
        y=project_block(c,y,p,first=(i==0))
    if academic:
        ensure(135);y=section(c,y,'학부 개발 프로젝트')
        for i,p in enumerate(academic):
            ensure(project_block_height(p)+15)
            y=project_block(c,y,p,True,first=(i==0))
    if profile['name']=='validation':
        ensure(125);y=combined_credentials_awards(c,y,data)
    else:
        ensure(145);y=combined_credentials_awards(c,y,data)
    if y<BOTTOM:raise RuntimeError(f'페이지 하단 넘침: {profile["name"]} y={y:.1f}')
    c.save()
    return {'path':str(out),'font':font_used,'pages':page,'last_page_bottom':round(y,1)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',default='all');ap.add_argument('--data',default=str(ROOT/'data/master.json'));ap.add_argument('--out',default=str(ROOT/'output'));ap.add_argument('--save-version',action='store_true');args=ap.parse_args()
    data=load_json(args.data);font=fonts();outdir=Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
    if args.profile=='all': profiles=['developer','validation']
    else:profiles=[args.profile]
    for name in profiles:
        p=load_json(ROOT/'profiles'/f'{name}.json')
        if 'extends' in p:
            base=load_json(ROOT/'profiles'/f"{p['extends']}.json")
            base.update({k:v for k,v in p.items() if k not in ('extends','summary_override')})
            if p.get('summary_override'):base['summary']=p['summary_override']
            p=base
        out=outdir/f'resume_{name}.pdf';result=build(data,p,out,font)
        if args.save_version:
            stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S');v=outdir/'history';v.mkdir(exist_ok=True);shutil.copy2(out,v/f'{stamp}_{out.name}')
        print(json.dumps(result,ensure_ascii=False))
    if font!='Pretendard':print('WARNING: Pretendard not installed; using NanumBarunGothic fallback. Set PRETENDARD_DIR to your local licensed font directory.',file=sys.stderr)
if __name__=='__main__':main()
