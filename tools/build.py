#!/usr/bin/env python3
"""把《建设项目环评分类管理名录修订对照》.docx 构建为静态页面 index.html。

用法：  python tools/build.py  你的文档.docx
依赖：  pip install python-docx
输出：  仓库根目录的 index.html（样式与脚本在 assets/ 中）
"""
import sys, re, html, pathlib
from difflib import SequenceMatcher
import docx
from docx.text.paragraph import Paragraph

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = html.escape

# ───────────────────────── 1. 读取 docx ─────────────────────────
def load(path):
    d = docx.Document(path)
    rels = {k: v.target_ref for k, v in d.part.rels.items() if 'hyperlink' in v.reltype}
    plain = lambda c: '\n'.join(p.text.strip() for p in c.paragraphs if p.text.strip())

    def lines(c):
        out = []
        for p in c.paragraphs:
            runs = [r for r in p.runs if r.text]
            if not runs: continue
            if len(runs) >= 2 and runs[0].bold:
                out.append((runs[0].text.strip(), ''.join(r.text for r in runs[1:]).strip()))
            else:
                out.append(('', ''.join(r.text for r in runs).strip()))
        return out

    paras = d.paragraphs
    D = dict(title=paras[0].text.strip(), subtitle=paras[1].text.strip(),
             intro=paras[2].text.strip(), source=paras[3].text.strip())
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    rid = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id'
    D['links'] = [(''.join(t.text for t in h.iter(ns + 't')), rels[h.get(rid)])
                  for h in d.element.body.iter(ns + 'hyperlink')]
    # 各小节说明文字
    ctx, cur = {}, None
    for ch in d.element.body.iterchildren():
        if ch.tag.endswith('}p'):
            p = Paragraph(ch, d)
            if p.style.name.startswith('Heading'): cur = p.text.strip(); ctx[cur] = []
            elif cur and p.text.strip(): ctx[cur].append(p.text.strip())
    D['ctx'] = ctx
    T = d.tables
    D['quick'] = [[plain(c) for c in r.cells] for r in T[0].rows[1:]]
    D['prov'] = [[plain(c) for c in r.cells] for r in T[1].rows[1:]]
    D['nuclear'] = ([plain(c) for c in T[2].rows[0].cells], [[plain(c) for c in r.cells] for r in T[2].rows[1:]])
    D['removed'] = [[plain(c) for c in r.cells] for r in T[3].rows[1:]]
    D['chapters'] = ([plain(c) for c in T[4].rows[0].cells], [[plain(c) for c in r.cells] for r in T[4].rows[1:]])
    groups = ['农业 采矿与食品制造', '纺织 轻工 化工与医药', '建材 冶炼 装备与资源利用',
              '电力 水务 环境治理和社会服务', '水利 交通和通用工序', '海洋工程及核与辐射']
    D['industry'] = []
    for gi, t in enumerate(T[5:11]):
        items = []
        for r in t.rows[1:]:
            c0 = [p.text.strip() for p in r.cells[0].paragraphs if p.text.strip()]
            m = re.match(r'^新\s*(\d+)\s+(.*)$', c0[0])
            no, name = (m.group(1), m.group(2)) if m else ('', c0[0])
            oldref = re.sub(r'^旧\s*', '', c0[1]) if len(c0) > 1 else ''
            items.append(dict(no=no, name=name, oldref=oldref, old=lines(r.cells[1]),
                              new=lines(r.cells[2]), note=plain(r.cells[3])))
        D['industry'].append((groups[gi], items))
    D['checked'] = [[plain(c) for c in r.cells] for r in T[11].rows[1:]]
    return D

# ───────────────────────── 2. 差异（修订标记）─────────────────────────
TOK = re.compile(r'\d+(?:\.\d+)?|[A-Za-z]+|\s+|.', re.S)

def ops_for(a, b):
    ta, tb = TOK.findall(a), TOK.findall(b)
    sm = SequenceMatcher(None, ta, tb, autojunk=False)
    if sm.ratio() < 0.4: return ta, tb, None
    ops = [list(o) for o in sm.get_opcodes()]
    # 夹在两处改动之间的单字相同片段并入改动，避免“碎屑”
    for k in range(1, len(ops) - 1):
        o = ops[k]
        if o[0] == 'equal' and ops[k-1][0] != 'equal' and ops[k+1][0] != 'equal' and (o[2] - o[1]) <= 2:
            o[0] = 'replace'
    merged = []
    for o in ops:
        if merged and merged[-1][0] != 'equal' and o[0] != 'equal':
            m = merged[-1]; m[2], m[4] = o[2], o[4]; m[0] = 'replace'
        else: merged.append(o)
    return ta, tb, merged

def diff_pair(a, b):
    """返回 (旧版HTML, 新版HTML)"""
    if a == b: return E(a), E(b)
    ta, tb, ops = ops_for(a, b)
    if ops is None: return E(a), E(b)
    ha, hb = [], []
    for tag, i1, i2, j1, j2 in ops:
        sa, sb = ''.join(ta[i1:i2]), ''.join(tb[j1:j2])
        if tag == 'equal': ha.append(E(sa)); hb.append(E(sb))
        else:
            if sa: ha.append('<del>%s</del>' % E(sa))
            if sb: hb.append('<ins>%s</ins>' % E(sb))
    return ''.join(ha), ''.join(hb)

def inline_redline(a, b):
    """合并成一行的修订标记（首屏示例）"""
    ta, tb, ops = ops_for(a, b)
    out = []
    for tag, i1, i2, j1, j2 in ops:
        sa, sb = ''.join(ta[i1:i2]), ''.join(tb[j1:j2])
        if tag == 'equal': out.append(E(sb))
        else:
            if sa: out.append('<del>%s</del>' % E(sa))
            if sb: out.append('<ins>%s</ins>' % E(sb))
    return ''.join(out)

# ───────────────────────── 3. 小部件 ─────────────────────────
ITEMS = set()
TAG_CLASS = {'报告书': 't-shu', '报告表': 't-biao', '登记表': 't-ji', '敏感区': 't-min', '范围': 't-fan'}

def xref(text):
    """转义并把“新123”变成条目锚点链接（仅当该条目在页面中存在）"""
    s = E(text).replace('\n', '<br>')
    return re.sub(r'新(\d{1,3})(?!\d)',
                  lambda m: ('<a class="xref" href="#n%s">新%s</a>' % (m.group(1), m.group(1)))
                  if m.group(1) in ITEMS else m.group(0), s)

def tag(label):
    return '<span class="tag %s">%s</span>' % (TAG_CLASS.get(label, 't-fan'), E(label))

def line(label, inner):
    if not label: return '<div class="ln nolabel"><span class="tx">%s</span></div>' % inner
    return '<div class="ln">%s<span class="tx">%s</span></div>' % (tag(label), inner)

def pair_lines(old, new):
    """按标签配对两侧各行并生成带差异的 HTML"""
    used = set(); pairs = []
    for ln, tx in new:
        m = next((i for i, (ol, ot) in enumerate(old) if i not in used and ol == ln), None)
        if m is not None: used.add(m)
        pairs.append(m)
    ohtml = [None] * len(old); nhtml = []
    for (ln, tx), m in zip(new, pairs):
        if m is None:
            nhtml.append(line(ln, '<ins>%s</ins>' % E(tx)) if tx else line(ln, ''))
        else:
            ha, hb = diff_pair(old[m][1], tx); ohtml[m] = line(old[m][0], ha); nhtml.append(line(ln, hb))
    for i, (ol, ot) in enumerate(old):
        if ohtml[i] is None: ohtml[i] = line(ol, '<del>%s</del>' % E(ot))
    return ''.join(ohtml), ''.join(nhtml)

def split_pos(s):
    parts = re.split(r'\s{2,}', s, maxsplit=1)
    return (parts[0], parts[1]) if len(parts) == 2 else (s, '')

def row(id_, head_html, old_html, new_html, note_html, oldh, newh, tiers=None):
    return ('<article class="row ent"%s%s>'
            '<header class="rh">%s</header>'
            '<div class="cols">'
            '<div class="cell old" data-h="%s">%s</div>'
            '<div class="cell new" data-h="%s">%s</div></div>'
            '%s</article>') % (
        ' id="%s"' % id_ if id_ else '', ' data-tiers="%s"' % tiers if tiers is not None else '',
        head_html, oldh, old_html, newh, new_html,
        ('<p class="note"><b>判定要点</b>%s</p>' % note_html) if note_html else '')

def colhead(a, b):
    return '<div class="colhead" aria-hidden="true"><span>%s</span><span>%s</span></div>' % (E(a), E(b))

def plain_table(head, rows, xcols=(0,), cls=''):
    h = ''.join('<th scope="col">%s</th>' % E(x) for x in head)
    b = ''.join('<tr class="ent">%s</tr>' % ''.join(
        '<td>%s</td>' % (xref(c) if i in xcols else E(c).replace('\n', '<br>')) for i, c in enumerate(r)) for r in rows)
    return '<div class="tablewrap"><table class="plain %s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, h, b)

# ───────────────────────── 4. 组装页面 ─────────────────────────
def build(D):
    for _, items in D['industry']:
        for it in items: ITEMS.add(it['no'])
    n_ind = sum(len(i) for _, i in D['industry'])
    ctx = D['ctx']
    parts = {}

    # —— 首屏示例：新120 污水处理（真实条目）
    it120 = next(i for _, items in D['industry'] for i in items if i['no'] == '120')
    od, nd = dict(it120['old']), dict(it120['new'])
    spec = []
    for lab in ('报告书', '报告表'):
        a, b = od[lab], nd[lab]
        if lab == '报告表':
            a, b = a.split('；')[0], b.split('；')[0]
        spec.append('<div class="ln">%s<span class="tx">%s</span></div>' % (tag(lab), inline_redline(a, b)))
    parts['SPECIMEN'] = ('<a class="spec-head" href="#n120"><span class="no">新 120</span>'
                         '<span class="nm">%s</span></a>%s') % (E(it120['name']), ''.join(spec))

    # —— 副标题、来源
    parts['SUBTITLE'] = ''.join('<li>%s</li>' % E(x.strip()) for x in D['subtitle'].split('｜'))
    parts['TITLE'] = E(D['title'])
    t = D['title']
    parts['TITLE_HTML'] = (E(t[:-4]) + '<span>修订对照</span>') if t.endswith('修订对照') else E(t)
    parts['INTRO'] = E(D['intro'])
    tail = D['source'].split('全文。', 1)[1] if '全文。' in D['source'] else ''
    parts['LINKS'] = ''.join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(u), E(t)) for t, u in D['links'])
    parts['SOURCE_TAIL'] = E(tail)

    # —— 导航
    nav = [('s1', '一', '主要变化速查', []), ('s2', '二', '正文条文和表后说明', []),
           ('s3', '三', '取消单列和部分移出项目', []),
           ('s4', '四', '行业项目逐项修订对照',
            [('g%d' % (i + 1), t, len(items)) for i, (t, items) in enumerate(D['industry'])]),
           ('s5', '五', '核对范围', [])]
    side, pills = [], []
    for sid, num, name, subs in nav:
        sub = ''
        if subs: sub = '<ul>%s</ul>' % ''.join('<li><a href="#%s">%s<small>%d</small></a></li>' % (g, E(t), n) for g, t, n in subs)
        side.append('<li><a href="#%s"><i>%s</i>%s</a>%s</li>' % (sid, num, E(name), sub))
        pills.append('<a href="#%s">%s %s</a>' % (sid, num, E(name)))
    parts['SIDENAV'] = ''.join(side)
    parts['PILLS'] = ''.join(pills)

    H = lambda sid, num, name: '<h2><span class="num">%s</span><span>%s</span></h2>' % (num, E(name))

    # —— 一 速查
    q = ''.join('<article class="q ent"><h3 class="q-area">%s</h3><p class="q-chg">%s</p><p class="q-ref">%s</p></article>'
                % (E(a), E(c), xref(r)) for a, c, r in D['quick'])
    notes = ''.join('<p>%s</p>' % E(p) for p in ctx['版本与读表方式'])
    legend = ('<div class="legend"><div><b>标签</b>%s%s%s%s%s</div>'
              '<div><b>差异</b><span class="ex">日处理<del>10万吨</del><ins>2万吨</ins>及以上</span></div></div>') % (
        tag('报告书'), tag('报告表'), tag('登记表'), tag('敏感区'), tag('范围'))
    s1 = ('<section class="sec" id="s1">%s<div class="quick">%s</div>'
          '<div class="ent readme"><h3>版本与读表方式</h3>%s'
          '<p class="legend-note">标签的轻重对应管理等级：实心为报告书，描边为报告表，虚线为登记表。'
          '在对照栏中，旧版删去的内容画删除线，新版新增或改动的内容以荧光笔标出（可在顶栏关闭）。</p>%s</div></section>') % (
        H('s1', '一', '主要变化速查'), q, notes, legend)

    # —— 二 条文
    rows = []
    for i, (pos, old, new, note) in enumerate(D['prov']):
        no, nm = split_pos(pos)
        ho, hn = diff_pair(old, new)
        head = '<span class="no txt">%s</span><span class="nm">%s</span>' % (E(no), E(nm))
        rows.append(row('p%d' % (i + 1), head, line('', ho), line('', hn), xref(note), '2021年版', '2027年版'))
    nuc_head, nuc_rows = D['nuclear']
    s2 = ('<section class="sec" id="s2">%s%s<div class="rows">%s</div>'
          '<h3 class="sub">核设施评价环节<span class="aside">新版附文</span></h3>%s</section>') % (
        H('s2', '二', '正文条文和表后说明'), colhead('2021年版', '2027年版'), ''.join(rows),
        plain_table(nuc_head, nuc_rows, xcols=(0,)))

    # —— 三 取消单列
    rows = []
    for oldpos, name, cond, dest in D['removed']:
        old_lines = []
        for ln_ in cond.split('\n'):
            lab, tx = split_pos(ln_)
            old_lines.append(line(lab, E(tx)) if tx and lab in TAG_CLASS else line('', E(ln_)))
        head = '<span class="nm solo">%s</span><span class="oldref">旧 %s</span>' % (E(name), E(re.sub(r'^旧\s*', '', oldpos)))
        rows.append(row('', head, ''.join(old_lines), line('', xref(dest)), '', '旧版条件', '新版去向'))
    ch_head, ch_rows = D['chapters']
    s3 = ('<section class="sec" id="s3">%s<p class="lead">%s</p>%s<div class="rows">%s</div>'
          '<h3 class="sub">章节和跨行业调整</h3>%s</section>') % (
        H('s3', '三', '新版取消单列和部分移出项目'), E(ctx['三  新版取消单列和部分移出项目'][0]),
        colhead('旧版条件', '新版去向'), ''.join(rows), plain_table(ch_head, ch_rows, xcols=(0, 1)))

    # —— 四 行业
    tfilter = ''.join('<button type="button" class="tag %s" aria-pressed="false" data-tier="%s">%s</button>'
                      % (TAG_CLASS[t], t, t) for t in ('报告书', '报告表', '登记表', '敏感区'))
    groups = []
    for gi, (gt, items) in enumerate(D['industry']):
        rows = []
        for it in items:
            oh, nh = pair_lines(it['old'], it['new'])
            tiers = ' '.join(sorted({l for l, _ in it['old'] + it['new'] if l in ('报告书', '报告表', '登记表', '敏感区')}))
            ref = it['oldref']
            oldref = ('<span class="oldref">%s</span>' % ('旧 ' + E(ref) if re.match(r'^\d', ref) else E(ref)))
            head = ('<a class="no" href="#n%s" title="复制此条目的链接"><sup>新</sup>%s</a><span class="nm">%s</span>%s'
                    % (it['no'], it['no'], E(it['name']), oldref))
            rows.append(row('n' + it['no'], head, oh, nh, xref(it['note']), '2021年版对应条件', '2027年版修订条件', tiers))
        groups.append('<div class="grp" id="g%d"><h3 class="sub">%s<span class="count">%d 项</span></h3>%s<div class="rows">%s</div></div>'
                      % (gi + 1, E(gt), len(items), colhead('2021年版对应条件', '2027年版修订条件'), ''.join(rows)))
    s4 = ('<section class="sec" id="s4">%s<p class="lead">%s</p>'
          '<div class="toolbar js-only"><span>只看含有以下标签的条目</span><div class="tfilters">%s</div></div>%s</section>') % (
        H('s4', '四', '行业项目逐项修订对照'), E(ctx['四  行业项目逐项修订对照'][0]), tfilter, ''.join(groups))

    # —— 五 核对范围
    rng, why = D['checked'][0]
    pairs = [p.strip() for p in rng.split('·') if p.strip()]
    chips = ''.join('<li><span>新 %s</span><i>⇐</i><span>旧 %s</span></li>' % tuple(p.split('⇐')) for p in pairs)
    s5 = ('<section class="sec" id="s5">%s<p class="lead">%s</p>'
          '<div class="ent same"><ul class="pairs" aria-label="新版项号 ⇐ 旧版项号">%s</ul><p class="why"><b>核查口径</b>%s</p></div></section>') % (
        H('s5', '五', '核对范围'), E(ctx['五  核对范围'][0]), chips, E(why))

    parts['MAIN'] = s1 + s2 + s3 + s4 + s5
    parts['TOTAL'] = str(n_ind)
    return parts

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    D = load(sys.argv[1])
    parts = build(D)
    tpl = (ROOT / 'tools' / 'template.html').read_text(encoding='utf-8')
    for k, v in parts.items(): tpl = tpl.replace('{{%s}}' % k, v)
    assert '{{' not in tpl, re.findall(r'\{\{\w+\}\}', tpl)
    (ROOT / 'index.html').write_text(tpl, encoding='utf-8')
    print('OK → index.html  (%d KB)' % ((ROOT / 'index.html').stat().st_size // 1024))

if __name__ == '__main__':
    main()
