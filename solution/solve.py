#!/usr/bin/env python3
"""参考解：枚举整数体积向量并按公开 R5--R7 规则选择最优配方。"""
import json, math, os, sys, tempfile
from decimal import Decimal, ROUND_HALF_UP

def fail(): raise SystemExit(2)
def dup(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValueError("duplicate")
        d[k]=v
    return d

def main(argv):
    if len(argv)!=3: fail()
    src,dst=argv[1:]
    try:
        with open(src,encoding='utf-8') as f: x=json.load(f,object_pairs_hook=dup)
        if not isinstance(x,dict) or set(x)!={'stocks','target_volume_ml','target_ph','max_cost_cents'}: fail()
        stocks=x['stocks']; tv=x['target_volume_ml']; tph=x['target_ph']; budget=x['max_cost_cents']
        if isinstance(tv,bool) or not isinstance(tv,int) or not 1<=tv<=40: fail()
        if isinstance(budget,bool) or not isinstance(budget,int) or not 0<=budget<=400000: fail()
        if isinstance(tph,bool) or not isinstance(tph,(int,float)) or not math.isfinite(tph) or not 0<=tph<=14: fail()
        if not isinstance(stocks,list) or not 1<=len(stocks)<=6: fail()
        seen=set(); ss=[]
        for s in stocks:
            if not isinstance(s,dict) or set(s)!={'stock_id','acid_mmol_per_ml','base_mmol_per_ml','cost_cents_per_ml','max_volume_ml'}: fail()
            sid=s['stock_id']
            if not isinstance(sid,str) or not 1<=len(sid)<=12 or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-' for c in sid) or sid in seen: fail()
            seen.add(sid)
            a,b=s['acid_mmol_per_ml'],s['base_mmol_per_ml']; c,m=s['cost_cents_per_ml'],s['max_volume_ml']
            if any(isinstance(z,bool) or not isinstance(z,(int,float)) or not math.isfinite(z) or not 0<=z<=100 for z in (a,b)) or a==0 and b==0: fail()
            if isinstance(c,bool) or not isinstance(c,int) or not 0<=c<=10000 or isinstance(m,bool) or not isinstance(m,int) or not 0<=m<=40: fail()
            ss.append((sid,float(a),float(b),c,m))
        best=None
        vec=[0]*len(ss)
        def rec(i,left):
            nonlocal best
            if i==len(ss)-1:
                v=left
                if v<0 or v>ss[i][4]: return
                vec[i]=v
                A=sum(vec[j]*ss[j][1] for j in range(len(ss))); B=sum(vec[j]*ss[j][2] for j in range(len(ss)))
                if not A>0 or not B>0: return
                ph=6.35+math.log10(B/A)
                if not math.isfinite(ph) or abs(ph-float(tph))>0.01+1e-12: return
                cost=sum(vec[j]*ss[j][3] for j in range(len(ss)))
                if cost>budget:return
                key=(cost,tuple(vec))
                if best is None or key<best[0]: best=(key,A,B,ph)
                return
            for v in range(min(ss[i][4],left)+1):
                vec[i]=v; rec(i+1,left-v)
        rec(0,tv)
        if best is None: fail()
        _,A,B,ph=best; volumes=list(best[0][1]); cost=best[0][0]
        q=Decimal(str(ph)).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
        out={'target_volume_ml':tv,'target_ph':tph,'total_volume_ml':sum(volumes),'total_acid_mmol':A,'total_base_mmol':B,'computed_ph':float(q),'total_cost_cents':cost,'stocks':[{'stock_id':ss[i][0],'volume_ml':volumes[i]} for i in range(len(ss))]}
        data=json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n'
        parent=os.path.dirname(os.path.abspath(dst)) or '.'; fd,tmp=tempfile.mkstemp(prefix='.buffer-',suffix='.tmp',dir=parent)
        try:
            with os.fdopen(fd,'w',encoding='utf-8',newline='') as f: f.write(data); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,dst)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    except Exception: fail()
if __name__=='__main__': main(sys.argv)
