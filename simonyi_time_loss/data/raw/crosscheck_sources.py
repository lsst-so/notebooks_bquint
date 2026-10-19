import re, glob, sys, csv
def parse(path):
    rows={}
    for line in open(path, encoding='utf-8'):
        if not line.startswith('| 20'): continue
        c=[x.strip() for x in line.strip().strip('|').split('|')]
        if len(c)<7: continue
        c[0]=c[0][:10]
        rows[c[0]]=dict(link=c[1],status=c[2],pw=c[3],pf=c[4],ev=c[5],tk=c[6])
    return rows
def f(x):
    try: return float(x)
    except: return None
s1={}; s2={}
for p in sorted(glob.glob('in/tailgate_sweep_*.md')): s1.update(parse(p))
for p in sorted(glob.glob('in/nightlog_sweep_*.md')): s2.update(parse(p))
days=[d for d in sorted(set(s1)|set(s2)) if '2025-10-25'<=d<='2026-07-14']
out=[]
for d in days:
    a=s1.get(d); b=s2.get(d)
    if not a or not b:
        out.append((d,'MISSING', a['status'] if a else '—', b['status'] if b else '—','','','','file missing on one side')); continue
    flags=[]
    base=lambda x:x.split()[0]
    if base(a['status'])!=base(b['status']):
        if a['status']=='UNKNOWN': flags.append('S1 UNKNOWN → S2 '+b['status'])
        elif b['status']=='UNKNOWN': flags.append('S2 UNKNOWN')
        else: flags.append('STATUS DISAGREE')
    for k,n in (('pw','P(weather)'),('pf','P(fault)')):
        x,y=f(a[k]),f(b[k])
        if x is not None and y is not None and abs(x-y)>=0.4: flags.append(f'{n} {x} vs {y}')
    if flags: out.append((d,'; '.join(flags),a['status'],b['status'],a['pw'],b['pw'],a['pf'],b['pf'],a['ev'][:160],b['ev'][:160]))
with open('crosscheck.md','w') as fh:
    fh.write(f'# Source 1 vs Source 2 cross-check — {days[0]} → {days[-1]}\n\nS1 nights: {len(s1)}, S2 nights: {len(s2)}, both: {len(set(s1)&set(s2))}. Rows listed only where status differs or a probability differs by ≥ 0.4.\n\n')
    fh.write('| day_obs | flag | S1 status | S2 status | S1 P(w) | S2 P(w) | S1 P(f) | S2 P(f) | S1 evidence (trunc.) | S2 evidence (trunc.) |\n|---|---|---|---|---|---|---|---|---|---|\n')
    for r in out: fh.write('| '+' | '.join(str(x) for x in r[:10])+' |\n')
    both=[d for d in days if d in s1 and d in s2]
    agree=sum(1 for d in both if s1[d]['status'].split()[0]==s2[d]['status'].split()[0])
    fh.write(f'\nStatus agreement: {agree}/{len(both)} nights.\n')

    unk=[(d,s2[d]['status'],s2[d]['pw'],s2[d]['pf']) for d in both if s1[d]['status']=='UNKNOWN' and s2[d]['status']!='UNKNOWN']
    fh.write(f'\n## Source 1 UNKNOWN nights resolved by Source 2 ({len(unk)})\n\n| day_obs | S2 status | P(w) | P(f) |\n|---|---|---|---|\n')
    for r in unk: fh.write('| '+' | '.join(r)+' |\n')
    still=[d for d in both if s1[d]['status']=='UNKNOWN' and s2[d]['status']=='UNKNOWN']
    s2unk=[d for d in both if s2[d]['status']=='UNKNOWN' and s1[d]['status']!='UNKNOWN']
    fh.write(f'\nStill UNKNOWN in both: {", ".join(still) or "none"}.\nS2 UNKNOWN but S1 judged: {", ".join(s2unk) or "none"}.\n')
    dis=[d for d in both if s1[d]['status'].split()[0]!=s2[d]['status'].split()[0] and 'UNKNOWN' not in (s1[d]['status'],s2[d]['status'])]
    from collections import Counter
    pat=Counter(f"S1 {s1[d]['status'].split()[0]} vs S2 {s2[d]['status'].split()[0]}" for d in dis)
    fh.write('Disagreement patterns: '+', '.join(f'{k} ×{v}' for k,v in pat.most_common())+'.\n')
    fh.write(f'Real status disagreements (neither UNKNOWN): {len(dis)}.\n')
print(open('crosscheck.md').read())
