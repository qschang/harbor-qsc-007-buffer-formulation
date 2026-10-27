import importlib.util, json, math, os, subprocess, sys, time
from pathlib import Path
from unittest.mock import patch
import pytest

SOL=Path(os.environ.get('APP',str(Path(__file__).parents[1]/'solution'/'solve.py')))
def run(inp,out,raw=None):
    src=out.with_name(out.stem+'-input.json')
    src.write_text(raw if raw is not None else json.dumps(inp,allow_nan=True,separators=(',',':')),encoding='utf-8')
    return subprocess.run([sys.executable,str(SOL),str(src),str(out)],capture_output=True,text=True)
def valid():
    return {'stocks':[{'stock_id':'A','acid_mmol_per_ml':1.0,'base_mmol_per_ml':0.1,'cost_cents_per_ml':3,'max_volume_ml':10},{'stock_id':'B','acid_mmol_per_ml':0.1,'base_mmol_per_ml':1.0,'cost_cents_per_ml':2,'max_volume_ml':10}],'target_volume_ml':10,'target_ph':7.35,'max_cost_cents':100}
def assert_clean(tmp_path):
    forbidden=('.tmp','.partial','.report','.ledger','.summary','.checkpoint')
    assert not [p for p in tmp_path.iterdir() if any(p.name.endswith(s) or s in p.name for s in forbidden) and 'input.json' not in p.name]

def test_valid_optimal_and_schema(tmp_path):
    """R5/R6/R8：可行配方满足公式、预算并按公开顺序输出完整字段。"""
    o=tmp_path/'result.json'; p=run(valid(),o); assert p.returncode==0; d=json.loads(o.read_text()); assert list(d)==['target_volume_ml','target_ph','total_volume_ml','total_acid_mmol','total_base_mmol','computed_ph','total_cost_cents','stocks']; assert d['total_volume_ml']==10; assert math.isclose(d['total_acid_mmol'],1.0); assert math.isclose(d['total_base_mmol'],10.0); assert d['computed_ph']==7.35; assert d['total_cost_cents']<=100; assert_clean(tmp_path)
def test_log_ratio_direction(tmp_path):
    """R5：交换目标 pH 后按碱酸比的对数方向匹配。"""
    x=valid(); x['target_ph']=5.35; o=tmp_path/'ratio.json'; p=run(x,o); assert p.returncode==0; d=json.loads(o.read_text()); assert d['computed_ph']==5.35; assert d['total_acid_mmol']>d['total_base_mmol']; assert_clean(tmp_path)
def test_cost_tie_lexicographic(tmp_path):
    """R6：成本相同时按输入次序选取词典序最小体积向量。"""
    x={'stocks':[{'stock_id':'A','acid_mmol_per_ml':1,'base_mmol_per_ml':1,'cost_cents_per_ml':1,'max_volume_ml':5},{'stock_id':'B','acid_mmol_per_ml':1,'base_mmol_per_ml':1,'cost_cents_per_ml':1,'max_volume_ml':5}],'target_volume_ml':5,'target_ph':6.35,'max_cost_cents':20}; o=tmp_path/'tie.json'; p=run(x,o); assert p.returncode==0; assert [z['volume_ml'] for z in json.loads(o.read_text())['stocks']]==[0,5]; assert_clean(tmp_path)
def test_max_volume_boundary(tmp_path):
    """R2/R5：零库存上限仍允许由其余库存满足目标量。"""
    x=valid(); x['stocks'][0]['max_volume_ml']=0; o=tmp_path/'bound.json'; p=run(x,o); assert p.returncode==0; assert json.loads(o.read_text())['stocks'][0]['volume_ml']==0; assert_clean(tmp_path)
def test_infeasible_reject_absent(tmp_path):
    """R5/R8：不可行 pH 对不存在的目标拒绝且不产生副产物。"""
    x=valid(); x['target_ph']=14; o=tmp_path/'absent.json'; p=run(x,o); assert p.returncode!=0; assert not o.exists(); assert_clean(tmp_path)
def test_infeasible_reject_sentinel(tmp_path):
    """R5/R8：不可行 pH 对旧目标拒绝并保持 sentinel 字节。"""
    x=valid(); x['target_ph']=14; o=tmp_path/'sentinel.json'; o.write_bytes(b'OLD'); p=run(x,o); assert p.returncode!=0; assert o.read_bytes()==b'OLD'; assert_clean(tmp_path)
def test_invalid_duplicate_key(tmp_path):
    """R4/R8：重复 JSON 键对不存在目标拒绝且无残留。"""
    o=tmp_path/'dup.json'; raw='{"stocks":[],"stocks":[],"target_volume_ml":1,"target_ph":6,"max_cost_cents":1}'; p=run({},o,raw); assert p.returncode!=0; assert not o.exists(); assert_clean(tmp_path)
def test_duplicate_key_sentinel(tmp_path):
    """R4/R8：重复 JSON 键对旧目标拒绝且 sentinel 字节不变。"""
    o=tmp_path/'dup-sentinel.json'; o.write_bytes(b'KEEP'); raw='{"stocks":[],"stocks":[],"target_volume_ml":1,"target_ph":6,"max_cost_cents":1}'; p=run({},o,raw); assert p.returncode!=0; assert o.read_bytes()==b'KEEP'; assert_clean(tmp_path)
def test_nonfinite_reject_sentinel(tmp_path):
    """R3/R4/R8：非有限 pH 拒绝且保留旧目标字节。"""
    x=valid(); x['target_ph']=float('nan'); o=tmp_path/'nan.json'; o.write_bytes(b'KEEP'); p=run(x,o); assert p.returncode!=0; assert o.read_bytes()==b'KEEP'; assert_clean(tmp_path)
def test_extra_key_reject_absent(tmp_path):
    """R1/R4/R8：多余根键对不存在目标拒绝且无残留。"""
    x=valid(); x['extra']=1; o=tmp_path/'extra.json'; p=run(x,o); assert p.returncode!=0; assert not o.exists(); assert_clean(tmp_path)
def test_extra_key_reject_sentinel(tmp_path):
    """R1/R4/R8：多余根键对旧目标拒绝且 sentinel 字节不变。"""
    x=valid(); x['extra']=1; o=tmp_path/'extra-sentinel.json'; o.write_bytes(b'KEEP'); p=run(x,o); assert p.returncode!=0; assert o.read_bytes()==b'KEEP'; assert_clean(tmp_path)
def test_boolean_numeric_reject(tmp_path):
    """R3/R4/R8：布尔体积拒绝且旧目标保持不变。"""
    x=valid(); x['target_volume_ml']=True; o=tmp_path/'bool.json'; o.write_bytes(b'KEEP'); p=run(x,o); assert p.returncode!=0; assert o.read_bytes()==b'KEEP'; assert_clean(tmp_path)
def test_deterministic_bytes(tmp_path):
    """R8：相同输入两次执行产生逐字节相同台账。"""
    x=valid(); a=tmp_path/'one.json'; b=tmp_path/'two.json'; p1=run(x,a); p2=run(x,b); assert p1.returncode==0; assert p2.returncode==0; assert a.read_bytes()==b.read_bytes(); assert_clean(tmp_path)
def test_budget_boundary(tmp_path):
    """R6/R8：预算允许时发布，预算不足时拒绝且目标缺失。"""
    x=valid(); o=tmp_path/'budget-ok.json'; p=run(x,o); assert p.returncode==0; x['max_cost_cents']=0; o2=tmp_path/'budget-no.json'; p2=run(x,o2); assert p2.returncode!=0; assert not o2.exists(); assert_clean(tmp_path)
def test_performance_bound(tmp_path):
    """性能/R2：六种库存和四十毫升规模在五秒内求解。"""
    x={'stocks':[{'stock_id':chr(65+i),'acid_mmol_per_ml':1,'base_mmol_per_ml':0.1,'cost_cents_per_ml':i+1,'max_volume_ml':40} for i in range(6)],'target_volume_ml':40,'target_ph':5.35,'max_cost_cents':400000}; o=tmp_path/'stress.json'; t=time.monotonic(); p=run(x,o); elapsed=time.monotonic()-t; assert p.returncode==0; assert elapsed<5; assert json.loads(o.read_text())['total_volume_ml']==40; assert_clean(tmp_path)
def test_late_invalid_preserves_old(tmp_path):
    """R2/R4/R8：末尾库存成本类型非法时旧目标字节完整且无副产物。"""
    x=valid(); x['stocks'][-1]['cost_cents_per_ml']=1.5; o=tmp_path/'late.json'; o.write_bytes(b'OLD'); p=run(x,o); assert p.returncode!=0; assert o.read_bytes()==b'OLD'; assert_clean(tmp_path)
def test_final_replace_failure_rolls_back(tmp_path):
    """R8：真实最终 os.replace 边界失败时非零退出、旧字节保留且清理临时物。"""
    spec=importlib.util.spec_from_file_location('candidate_solver',SOL); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); src=tmp_path/'fault-input.json'; src.write_text(json.dumps(valid()),encoding='utf-8'); out=tmp_path/'fault.json'; out.write_bytes(b'OLD');
    with patch.object(mod.os,'replace',side_effect=OSError('injected replace failure')):
        with pytest.raises(SystemExit) as exc: mod.main(['solve.py',str(src),str(out)])
        assert exc.value.code!=0
    assert out.read_bytes()==b'OLD'; assert not list(tmp_path.glob('.buffer-*')); assert_clean(tmp_path)


