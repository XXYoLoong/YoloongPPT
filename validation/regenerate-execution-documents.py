"""Apply user-authorized execution policy without changing baseline requirements."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / '.tmp/execution-revision'
POLICY = json.loads((ROOT / 'validation/authorized-execution-policy-20261012.json').read_text('utf-8'))
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
def q(name): return f'{{{W}}}{name}'
def sha(data): return hashlib.sha256(data).hexdigest()
def text(node): return ''.join(node.itertext()) if node is not None else ''
def para(content='', *, heading=False, bold=False, page_break=False):
    p = E.Element(q('p')); pr = E.SubElement(p,q('pPr'))
    if heading:
        E.SubElement(pr,q('pStyle')).set(q('val'),'Heading1')
        E.SubElement(pr,q('keepNext'))
    if page_break: E.SubElement(pr,q('pageBreakBefore'))
    E.SubElement(pr,q('spacing'),{q('before'):'80' if heading else '0',q('after'):'100',q('line'):'276',q('lineRule'):'auto'})
    r=E.SubElement(p,q('r')); rp=E.SubElement(r,q('rPr'))
    E.SubElement(rp,q('color')).set(q('val'),'000000')
    E.SubElement(rp,q('rFonts'),{q('ascii'):'Calibri',q('hAnsi'):'Calibri',q('eastAsia'):'Noto Sans CJK SC'})
    E.SubElement(rp,q('sz')).set(q('val'),'26' if heading else '20')
    if heading or bold:E.SubElement(rp,q('b'))
    E.SubElement(r,q('t')).text=content
    return p

def main():
    src = TMP/'before-AI_PPT_PDR_完整需求定义_V0.3.docx'
    with ZipFile(src) as z:
        root=E.fromstring(z.read('word/document.xml')); before=copy.deepcopy(root)
        body=root.find('w:body',NS); original_children=list(body)
        subtitle=body[1]; ts=subtitle.findall('.//w:t',NS)
        ts[0].text='PDR 式需求基线 V0.3  执行修订 EXEC-20261012-01  2026-10-12'
        for t in ts[1:]:t.text=''
        # Add two execution pages before the unchanged numbered requirements.
        at=4; added=[]
        added.append(para('执行主体与开源融合',heading=True,page_break=True))
        added.append(para('本次用户授权调整实施方式。全部原需求、任务、依赖、验收及 GOV-009 范围继续有效。'))
        for i,s in enumerate(POLICY['sections']):
            if i==7:added.append(para('整体交付与验收',heading=True,page_break=True))
            added.append(para(s['title'],bold=True))
            added.append(para(s['text']))
        added.append(para('Docling 来源：https://github.com/docling-project/docling；文档：https://docling-project.github.io/docling/。本轮登记执行路线，集成版本与模型许可按 GOV-010、RES-032、SEC-013 冻结并记录。'))
        for n in added:body.insert(at,n);at+=1
        # Start unchanged numbered requirements on a new page after the policy.
        first=original_children[4]; pr=first.find('w:pPr',NS)
        if pr.find('w:pageBreakBefore',NS) is None:E.SubElement(pr,q('pageBreakBefore'))
        revised=E.tostring(root,xml_declaration=True,encoding='UTF-8',standalone=True)
        out=TMP/'after-AI_PPT_PDR_完整需求定义_V0.3.docx'
        with ZipFile(out,'w') as target:
            for info in z.infolist():target.writestr(copy.copy(info),revised if info.filename=='word/document.xml' else z.read(info.filename))
        # Original requirement prose, all tables, numbering and all other parts preserved.
        for i,node in enumerate(original_children):
            if i==1:continue
            expected=copy.deepcopy(list(before.find('w:body',NS))[i]); actual=copy.deepcopy(node)
            if i==4:
                for n in actual.findall('w:pPr/w:pageBreakBefore',NS):n.getparent().remove(n)
                for n in expected.findall('w:pPr/w:pageBreakBefore',NS):n.getparent().remove(n)
            assert E.tostring(expected)==E.tostring(actual),('Original body changed',i)
        assert len(before.findall('.//w:tbl',NS))==len(root.findall('.//w:tbl',NS))==13
        with ZipFile(out) as saved:
            assert all(z.read(n)==saved.read(n) for n in z.namelist() if n!='word/document.xml')
    goal=['# YoloongPPT 完整交付目标','',f'执行修订：{POLICY["revision_id"]}。用户授权日期：2026-10-12。开发主体：GPT-6.1 sol。','',
          '## 一、唯一目标与需求基线','',
          '依据根目录《AI_PPT_PDR_完整需求定义_V0.3.docx》和《AI_PPT_完整需求与任务矩阵_V0.3.xlsx》，完成可追溯、可运行、可验收的 AI PPT 系统。覆盖全部 308 条主需求、453 个可执行任务、S00–S44 主链路、DEC-001–040 决策节点、PPT-001–030 对象能力、PP-01–09 后端路线及 AC-001–030 验收场景。','',
          '真实输入通过统一任务入口、来源解析、内容与证据、决策、模板与素材、可编辑 PPTX 执行、渲染及结构/视觉/事实/可编辑性 QA，连接局部修订和再次验收。CLI、API、MCP、调试入口、已有 PPT 修改、安全、许可、可观察性、取消与失败恢复全部按原要求交付。','',
          '本文件组织执行，原 DOCX/XLSX 定义产品要求与验收。执行修订不新增或删除基线任务，不改写原依赖，不降低验收，不把 Unsupported、Partial、Untested、Blocked 当作必需能力完成。产品范围变化必须取得用户授权并关联原 ID。','',
          '## 二、GPT-6.1 sol 自主执行与开源复用','']
    for s in POLICY['sections']:
        goal.extend([f'### {s["title"]}','',s['text'],'',f'关联原 ID：{"、".join(s["ids"])}。',''])
    goal.extend(['## 三、必须实现的融合行为','',
        '1. 统一任务入口实际调用开源组件；将来源、能力、模板、对象、执行、问题及修订映射到现有 schema/ID/trace。单独上游脚本成功不能替代产品接入。',
        '2. 全量来源与冲突候选保存，生成、QA、修订及复查只消费已选事实快照。未决冲突、必需缺失、未知硬约束和无依据变换显式失败。假设和推算保留稳定 ID、前提、公式与可见标记，不回退全部原文。',
        '3. 资产使用真实登记文件与 asset_id；节点/边、图注、DPI、许可和裁切政策保留证据。模板使用真实布局与占位符，核对尺寸/hash/字体/品牌锁/安全区；保留母版、主题、媒体与未知部件。',
        '4. 容量处理完整保留标题、正文、表格单元格、单位、关键列、来源及假设；禁止静默裁剪、移正文到备注或缩到不可读。硬页数不足显式失败，宽表关键列沿用原声明。',
        '5. QA 与修订实际消费统一问题记录。RevisionPlan 执行前检查父 run、before spec、目标范围与锁。修改后实际渲染并独立复查，保持未选页/对象和原事实，P0=0不自动允许 final。',
        '6. 恢复核对原 PPTX、PDF/PNG、辅助文本、快照及 hash。默认 recheck 可发起新审查；只有明确 reuse_saved_review=true 且全部原契约一致才复用旧响应，不新增模型/渲染。显式复用缺有效证据时失败，不暗切 fresh review。','',
        '## 四、执行纪律与完成证据','',
        '每次恢复先检查 yoloongdevlop、工作区、上次提交、origin/yoloongdevlop 和上次未完成项，再读取当前涉及的原行及关联源码。保留用户改动。复用有效固定版本和运行证据，补测须由版本变化、失败或原验收证据缺口驱动。',
        '每个实际实现分组写明原 Task ID、未满足条件、具体修改、验证命令和结束条件，随后完成集成、验收、矩阵回填及版本保存；不中断为新的规划或研究材料任务。同轮只保留一个主集成目标和一个可独立推进的解阻事项，模块并行服务同一整体交付。',
        '需求主表 N:P、可执行任务 L:M、验收矩阵 G:J 按实际结果回填；同步受影响的 0-1全链路及剩余条件，核对总览公式缓存。任务新增执行元数据不改变其原动作、依赖、状态或验收。',
        '最终逐项核对全部原要求；保存实际输入、可编辑 PPTX、PDF/PNG、对象差异、来源事实、决策/执行 trace、QA、修订前后实物、失败/恢复记录、版本/许可与复现命令。实际未通过项继续列明，不能使用总结文字冲销。','',
        '## 五、环境与版本保存','',
        '产品运行环境保持项目 Docker Compose，命名空间 yoloongppt，使用 scripts/project.ps1 管理。当前运行时与路线按 ARCHITECTURE.md、requirements.lock 和镜像 digest；开源组件通过适配器或隔离服务接入，不能因主机工具版本擅改产品要求。',
        '任何操作前确认临时目录位于 F:；Docker 操作前确认实际数据盘位于 F:。项目代码、依赖、缓存、产物、日志及容器可写层/卷/构建缓存不得落 C:。密钥和 .env 不提交、不打印、不写日志或镜像。',
        '在 yoloongdevlop 保存实际变更，中文 commit 并推送 origin/yoloongdevlop，不 force-push。ailog/ 与 development-log/ 每包新建同名中文标题和本地时间戳的 UTF-8 日志；推送失败保留本地提交并准确记录。',
        '历史执行与证据由 Git、PROJECT_PLAN.md、当前实现与阶段收尾报告_20261012.md 和 validation/ 保留；旧阶段建议及复用偏好不能覆盖本次用户授权的自主融合交付要求。',''])
    (TMP/'after-GOAL.md').write_text('\n'.join(goal),encoding='utf-8',newline='\n')
    report={'revision_id':POLICY['revision_id'],'original_document_body_preserved_except_version':True,'tables':13,'unchanged_other_docx_parts':True,'new_policy_sections':14,'before_sha256':sha(src.read_bytes()),'after_sha256':sha(out.read_bytes()),'goal_sha256':sha((TMP/'after-GOAL.md').read_bytes()),'authorization':POLICY['authorization']}
    (ROOT/'validation/execution-document-preservation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
