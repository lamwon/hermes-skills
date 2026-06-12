# -*- coding: utf-8 -*-
"""
Skill Review Tool v1.0
一道审查 Hermes / Claude Code 技能的 8 维评分工具。
支持 GitHub 仓库 URL 或本地路径。
输出：终端评分摘要 + HTML 详细报告。
"""

import os, sys, json, re, urllib.request, base64, textwrap
from datetime import datetime

# ============================================================
# 8 维评分标准
# ============================================================
DIMENSIONS = [
    {
        "id": "code_quality",
        "name": "Code Quality",
        "name_cn": "代码质量",
        "weight": 1.0,
        "questions": [
            "代码语法是否正确，有无明显的 Python 语法错误？",
            "是否有完善的错误处理（try/except、网络重试）？",
            "是否有安全风险（如关闭 SSL 验证、硬编码密钥）？",
            "代码风格是否符合 PEP 8？变量命名是否清晰？",
        ],
        "good": "代码语法正确，有完善的错误处理和重试机制，无明显安全风险",
        "bad": "有语法错误，缺乏错误处理，存在安全风险"
    },
    {
        "id": "documentation",
        "name": "Documentation",
        "name_cn": "文档完整性",
        "weight": 1.0,
        "questions": [
            "README/SKILL.md 是否有清晰的标题和简介？",
            "是否有安装步骤、配置说明、使用示例？",
            "是否有参数说明、FAQ、对比表？",
            "是否有效果展示（示例图、badges）？",
        ],
        "good": "文档完整，包含简介、安装、使用、示例、FAQ、对比",
        "bad": "文档缺失或过于简略，缺乏使用说明"
    },
    {
        "id": "architecture",
        "name": "Architecture",
        "name_cn": "架构设计",
        "weight": 0.8,
        "questions": [
            "文件结构是否清晰？脚本是否独立可运行？",
            "是否有不必要的重复文件？",
            "依赖管理是否合理（是否零依赖或明确声明）？",
            "是否有 .gitignore 等工程化文件？",
        ],
        "good": "结构清晰，文件职责明确，有工程化配置",
        "bad": "文件冗余或缺失，依赖不明确"
    },
    {
        "id": "ux",
        "name": "User Experience",
        "name_cn": "用户体验",
        "weight": 0.9,
        "questions": [
            "安装步骤是否简单（一行命令？pip install？）？",
            "使用方式是否直观（参数是否合理？有无 --help）？",
            "输出信息是否友好（彩色输出、进度提示）？",
            "中文用户是否友好（中文文档、中文错误提示）？",
        ],
        "good": "安装简单，使用直观，输出友好",
        "bad": "安装复杂，使用不便，缺乏提示"
    },
    {
        "id": "error_handling",
        "name": "Error Handling",
        "name_cn": "错误处理",
        "weight": 0.8,
        "questions": [
            "API 调用失败时是否有重试机制？",
            "网络超时、限流(429)是否有处理？",
            "配置缺失时是否有清晰的错误提示？",
            "是否有边缘情况处理（空输入、特殊字符）？",
        ],
        "good": "完善的错误处理，所有失败场景都有应对",
        "bad": "错误发生时直接崩溃，无提示"
    },
    {
        "id": "portability",
        "name": "Portability",
        "name_cn": "跨平台兼容",
        "weight": 0.6,
        "questions": [
            "是否支持 Windows / macOS / Linux？",
            "路径处理是否跨平台（os.path.join vs 硬编码 /）？",
            "编码处理是否正确（UTF-8 vs GBK）？",
            "是否有平台特定的依赖？",
        ],
        "good": "全平台兼容，路径和编码处理正确",
        "bad": "仅限特定平台，跨平台会报错"
    },
    {
        "id": "maintainability",
        "name": "Maintainability",
        "name_cn": "可维护性",
        "weight": 0.6,
        "questions": [
            "代码是否有注释？函数是否有 docstring？",
            "配置是否集中管理（常量 vs 散落各处）？",
            "是否有版本号或 changelog？",
            "代码长度是否合理（单文件 vs 合理拆分）？",
        ],
        "good": "代码注释充分，配置集中，易于修改",
        "bad": "无注释，配置分散，难以维护"
    },
    {
        "id": "innovation",
        "name": "Innovation & Value",
        "name_cn": "创新与价值",
        "weight": 0.5,
        "questions": [
            "是否解决了真实痛点？",
            "与现有方案相比是否有独特优势？",
            "是否有对比表证明其价值？",
            "创意和技术实现是否有亮点？",
        ],
        "good": "解决了真实问题，有独特价值主张",
        "bad": "缺乏差异化，可被轻易替代"
    },
]


def fetch_from_github(repo_url):
    """从 GitHub URL 获取仓库内容"""
    # Parse owner/repo from URL
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", repo_url)
    if not m:
        return None, "无法解析 GitHub URL"
    owner, repo_name = m.group(1), m.group(2)
    
    base = f"https://api.github.com/repos/{owner}/{repo_name}"
    req = urllib.request.Request(base, headers={"User-Agent": "hermes-agent"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        repo_info = json.loads(resp.read().decode())
    except Exception as e:
        return None, f"无法访问仓库: {e}"
    
    # Try to get SKILL.md and README.md
    files = {}
    for fname in ["SKILL.md", "README.md", "skill/SKILL.md"]:
        url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/main/{fname}"
        try:
            req2 = urllib.request.Request(url, headers={"User-Agent": "hermes-agent"})
            resp2 = urllib.request.urlopen(req2, timeout=10)
            files[fname] = resp2.read().decode()
        except:
            try:
                url2 = f"https://raw.githubusercontent.com/{owner}/{repo_name}/master/{fname}"
                req3 = urllib.request.Request(url2, headers={"User-Agent": "hermes-agent"})
                resp3 = urllib.request.urlopen(req3, timeout=10)
                files[fname] = resp3.read().decode()
            except:
                pass
    
    # Get repo contents list
    try:
        url3 = f"{base}/contents"
        req4 = urllib.request.Request(url3, headers={"User-Agent": "hermes-agent"})
        resp4 = urllib.request.urlopen(req4, timeout=10)
        contents = json.loads(resp4.read().decode())
    except:
        contents = []
    
    result = {
        "name": repo_info.get("name", repo_name),
        "full_name": repo_info.get("full_name", f"{owner}/{repo_name}"),
        "description": repo_info.get("description", ""),
        "stars": repo_info.get("stargazers_count", 0),
        "forks": repo_info.get("forks_count", 0),
        "language": repo_info.get("language", ""),
        "topics": repo_info.get("topics", []),
        "files": files,
        "contents": [x["name"] for x in contents if isinstance(x, dict)] if contents else [],
    }
    return result, None


def review_skill(repo_data):
    """执行 8 维审查"""
    content = ""
    content += repo_data["files"].get("SKILL.md", "")
    content += "\n\n"
    content += repo_data["files"].get("README.md", "")
    content += "\n\n"
    
    # For each file in the repo, try to fetch .py files
    py_files = {}
    for item_name in repo_data.get("contents", []):
        if item_name.endswith(".py"):
            owner, repo_name = repo_data["full_name"].split("/")
            for branch in ["main", "master"]:
                url = f"https://raw.githubusercontent.com/{owner}/{repo_name}/{branch}/{item_name}"
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "hermes-agent"})
                    resp = urllib.request.urlopen(req, timeout=5)
                    py_files[item_name] = resp.read().decode()
                    break
                except:
                    continue
    
    scores = {}
    findings = []
    suggestions = []
    
    for dim in DIMENSIONS:
        dim_id = dim["id"]
        score = 5.0  # 默认 5 分
        
        # Analyze based on content
        has_code = bool(py_files) or bool(re.findall(r"```python", content))
        has_readme = "SKILL.md" in repo_data["files"] or "README.md" in repo_data["files"]
        has_install = bool(re.search(r"install|pip |npm |git clone", content, re.I))
        has_examples = bool(re.search(r"example|示例|usage|用法|demo", content, re.I))
        has_toc = bool(re.search(r"# ", content))
        has_faq = bool(re.search(r"faq|FAQ|常见问题", content))
        has_help = bool(re.search(r"--help|-h|Usage", content))
        has_retry = bool(re.search(r"retry|重试|max_retries", content, re.I))
        has_error = bool(re.search(r"try:|except|HTTPError", content))
        has_gitignore = ".gitignore" in repo_data.get("contents", [])
        has_standalone = any(f.endswith(".py") for f in repo_data.get("contents", []))
        
        # Code Quality
        if dim_id == "code_quality":
            if not has_code: score = 2.0
            elif has_retry and has_error and not has_code: score = 6.0
            # Check for syntax errors
            syntax_ok = True
            for fname, fcontent in py_files.items():
                if "***" in fcontent or "TODO" in fcontent:
                    syntax_ok = False
                    break
            if has_retry: score += 1.0
            if has_error: score += 0.5
            if not has_retry and has_error: score -= 0.5
            if syntax_ok and has_standalone: score += 1.0
            score = min(max(score, 1.0), 10.0)
            
            if not has_retry:
                suggestions.append("添加网络重试机制，提高 API 调用稳定性")
            if not has_error:
                suggestions.append("增加 try/except 错误处理，避免直接崩溃")
            if not syntax_ok:
                findings.append("存在语法错误（如 ***/TODO 占位符未替换）")
                
        # Documentation
        elif dim_id == "documentation":
            if has_readme: score = 6.0
            if has_install: score += 1.0
            if has_examples: score += 1.0
            if has_faq: score += 0.5
            if has_toc: score += 0.5
            score = min(max(score, 1.0), 10.0)
            
            if not has_install:
                suggestions.append("文档缺少安装说明")
            if not has_examples:
                suggestions.append("文档缺少使用示例")
            if not has_faq:
                suggestions.append("建议添加 FAQ 章节解答常见问题")
                
        # Architecture
        elif dim_id == "architecture":
            if has_standalone: score = 6.0
            if has_gitignore: score += 1.0
            if has_code: score += 0.5
            if not has_standalone: score -= 1.0
            score = min(max(score, 1.0), 10.0)
            
            if not has_standalone:
                suggestions.append("脚本应提取为独立 .py 文件，方便用户直接运行")
            if not has_gitignore:
                suggestions.append("添加 .gitignore 排除输出文件和配置文件")
                
        # UX
        elif dim_id == "ux":
            if has_install: score = 6.0
            if has_help: score += 1.5
            if has_examples: score += 1.0
            if "中文" in content or "chinese" in content.lower(): score += 0.5
            score = min(max(score, 1.0), 10.0)
            
            if not has_help:
                suggestions.append("添加 --help 参数和用法说明")
                
        # Error Handling
        elif dim_id == "error_handling":
            if has_retry: score = 8.0
            elif has_error: score = 6.0
            else: score = 3.0
            score = min(max(score, 1.0), 10.0)
            
            if not has_retry:
                suggestions.append("增加指数退避重试机制应对 API 限流")
                
        # Portability
        elif dim_id == "portability":
            has_os_path = bool(re.search(r"os\.path\.join|Path\(|pathlib", content))
            has_utf8 = bool(re.search(r"utf-?8|encoding", content, re.I))
            if has_os_path: score += 1.5
            if has_utf8: score += 1.5
            if has_standalone: score += 0.5
            score = min(max(score, 1.0), 10.0)
            
            if not has_os_path:
                suggestions.append("使用 os.path.join 替代硬编码路径分隔符")
            if not has_utf8:
                suggestions.append("指定 UTF-8 编码避免 Windows GBK 兼容问题")
                
        # Maintainability
        elif dim_id == "maintainability":
            has_comments = bool(re.search(r"# |'''|\"\"\"", content))
            has_config_central = bool(re.search(r"=== 配置 ===|# Config|config =", content))
            if has_comments: score += 1.5
            if has_config_central: score += 1.5
            score = min(max(score, 1.0), 10.0)
            
            if not has_comments:
                suggestions.append("代码添加注释和函数说明")
            if not has_config_central:
                suggestions.append("配置项集中管理，方便修改")
                
        # Innovation
        elif dim_id == "innovation":
            topics = repo_data.get("topics", [])
            stars = repo_data.get("stars", 0)
            desc = repo_data.get("description", "")
            has_comparison = bool(re.search(r"对比|comparison|vs|alternatives?", content, re.I))
            
            if stars >= 100: score = 8.0
            elif stars >= 10: score = 7.0
            elif stars >= 1: score = 6.0
            else: score = 5.0
            
            if has_comparison: score += 1.0
            if desc: score += 0.5
            if topics: score += 0.5
            score = min(max(score, 1.0), 10.0)
            
            if not has_comparison:
                suggestions.append("添加与其他方案的对比表，突出差异化")
        
        scores[dim_id] = {
            "name": dim["name"],
            "name_cn": dim["name_cn"],
            "score": round(score, 1),
            "weight": dim["weight"],
            "weighted": round(score * dim["weight"], 1),
        }
    
    # 计算总分
    total_weighted = sum(s["weighted"] for s in scores.values())
    total_weight = sum(d["weight"] for d in DIMENSIONS)
    total_score = round(total_weighted / total_weight, 1)
    
    # 评级
    if total_score >= 9: rating = "S"
    elif total_score >= 8: rating = "A"
    elif total_score >= 7: rating = "B"
    elif total_score >= 5: rating = "C"
    else: rating = "D"
    
    return {
        "scores": scores,
        "total_score": total_score,
        "rating": rating,
        "suggestions": suggestions,
        "findings": findings,
        "repo_data": repo_data,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def generate_html(result):
    """生成 HTML 报告"""
    d = result["repo_data"]
    scores = result["scores"]
    total = result["total_score"]
    rating = result["rating"]
    
    # Color for rating
    rating_colors = {"S": "#FFD700", "A": "#00E676", "B": "#64B5F6", "C": "#FFB74D", "D": "#EF5350"}
    # Simplify: use gradient
    def score_color(s):
        if s >= 8: return "#43a047"
        if s >= 6: return "#ffa726"
        if s >= 4: return "#ff7043"
        return "#ef5350"
    
    rows = ""
    for dim in DIMENSIONS:
        s = scores[dim["id"]]
        bar_w = int(s["score"] * 10)
        color = score_color(s["score"])
        rows += f"""
        <tr>
            <td style="padding:10px 15px;font-weight:bold;color:#e0e0e0;border-bottom:1px solid #333;">{dim["name_cn"]}</td>
            <td style="padding:10px 15px;color:#aaa;border-bottom:1px solid #333;">{dim["name"]}</td>
            <td style="padding:10px 15px;border-bottom:1px solid #333;width:300px;">
                <div style="background:#333;border-radius:8px;height:20px;overflow:hidden;position:relative;">
                    <div style="background:{color};width:{bar_w}%;height:100%;border-radius:8px;transition:width 0.5s;"></div>
                </div>
            </td>
            <td style="padding:10px 15px;font-weight:bold;text-align:center;color:{color};border-bottom:1px solid #333;">{s["score"]}/10</td>
        </tr>"""
    
    # Suggestions
    sug_items = ""
    for i, sug in enumerate(result["suggestions"], 1):
        sug_items += f'<li style="margin:10px 0;color:#ccc;font-size:15px;">{i}. {sug}</li>'
    
    if not sug_items:
        sug_items = '<li style="color:#66bb6a;">暂无改进建议，技能质量很高！</li>'
    
    # Info
    info = f"""
    <table style="width:100%;border-collapse:collapse;margin:15px 0;">
        <tr><td style="padding:8px;color:#888;">仓库</td><td style="padding:8px;color:#eee;">{d["full_name"]}</td></tr>
        <tr><td style="padding:8px;color:#888;">描述</td><td style="padding:8px;color:#eee;">{d.get("description","无")}</td></tr>
        <tr><td style="padding:8px;color:#888;">Stars</td><td style="padding:8px;color:#FFD700;">{d.get("stars",0)}</td></tr>
        <tr><td style="padding:8px;color:#888;">Topics</td><td style="padding:8px;color:#64B5F6;">{', '.join(d.get("topics",["无"]))}</td></tr>
        <tr><td style="padding:8px;color:#888;">审查时间</td><td style="padding:8px;color:#eee;">{result["timestamp"]}</td></tr>
    </table>"""
    
    # Files
    files_str = ""
    for fname in d.get("contents", []):
        files_str += f'<span style="background:#2a2a2a;color:#888;padding:4px 12px;border-radius:12px;margin:4px;display:inline-block;font-size:13px;">{fname}</span>'
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skill Review Report - {d["full_name"]}</title>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,'Microsoft YaHei',sans-serif; background:#1a1a2e; color:#eee; }}
.container {{ max-width:800px; margin:0 auto; padding:20px; }}
.header {{ text-align:center; padding:40px 0 20px; }}
.header h1 {{ font-size:28px; color:#fff; }}
.header .subtitle {{ color:#888; margin-top:8px; font-size:15px; }}
.rating-badge {{ display:inline-block; width:80px; height:80px; line-height:80px; border-radius:50%;
    text-align:center; font-size:36px; font-weight:bold; margin:20px auto; }}
.score-number {{ font-size:48px; font-weight:bold; color:#fff; }}
.card {{ background:#16213e; border-radius:16px; padding:25px; margin:20px 0; }}
.card-title {{ font-size:18px; font-weight:bold; color:#fff; margin-bottom:15px; }}
table {{ width:100%; border-collapse:collapse; }}
th {{ padding:12px 15px; text-align:left; color:#888; border-bottom:2px solid #333; font-weight:normal; font-size:14px; }}
.suggestions {{ list-style:none; padding:0; }}
.footer {{ text-align:center; padding:30px; color:#555; font-size:13px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div style="font-size:14px;color:#888;margin-bottom:5px;">Skill Review Report</div>
        <h1>{d["full_name"]}</h1>
        <div class="subtitle">{d.get("description","")[:80]}</div>
        <div class="rating-badge" style="background:{rating_colors.get(rating,'#888')}20;color:{rating_colors.get(rating,'#888')};border:3px solid {rating_colors.get(rating,'#888')};">{rating}</div>
        <div class="score-number" style="color:{score_color(total)};">{total}</div>
        <div style="color:#888;font-size:14px;">/ 10 总分</div>
    </div>
    
    <div class="card">
        <div class="card-title"> 仓库信息</div>
        {info}
    </div>
    
    <div class="card">
        <div class="card-title"> 文件结构</div>
        <div>{files_str}</div>
    </div>
    
    <div class="card">
        <div class="card-title">  8 维评分</div>
        <table>
            <tr><th style="width:80px;">维度</th><th style="width:120px;">英文</th><th>得分</th><th style="width:50px;text-align:center;">分数</th></tr>
            {rows}
            <tr>
                <td colspan="4" style="padding:15px;text-align:center;font-weight:bold;font-size:18px;color:#fff;">
                    总分: <span style="color:{score_color(total)};">{total}/10</span> 评级: <span style="color:{rating_colors.get(rating,'#888')};">{rating}</span>
                </td>
            </tr>
        </table>
    </div>
    
    <div class="card">
        <div class="card-title">  改进建议</div>
        <ul class="suggestions">{sug_items}</ul>
    </div>
    
    <div class="footer">
        Generated by Hermes Skill Review Tool | {result["timestamp"]}
    </div>
</div>
</body>
</html>"""
    return html


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Skill Review - 审查 Hermes/Claude Code 技能")
    parser.add_argument("target", nargs="?", help="GitHub 仓库 URL 或本地目录路径")
    parser.add_argument("--html", "-H", action="store_true", help="生成 HTML 报告文件")
    parser.add_argument("--output", "-o", default="skill-review-report.html", help="HTML 报告输出路径")
    
    args = parser.parse_args()
    
    if not args.target:
        print("用法: python review_tool.py <github_url_or_local_path> [--html]")
        print("示例: python review_tool.py https://github.com/lamwon/hermes-image-generation-skill --html")
        return
    
    target = args.target
    
    # 从 GitHub 获取
    if "github.com" in target:
        print(f"[*] 正在从 GitHub 获取仓库: {target}")
        data, err = fetch_from_github(target)
        if err:
            print(f"[!] 错误: {err}")
            return
    else:
        # 本地路径模式
        print(f"[*] 正在读取本地目录: {target}")
        if not os.path.isdir(target):
            print(f"[!] 目录不存在: {target}")
            return
        files = {}
        contents = []
        for root, dirs, fnames in os.walk(target):
            for fname in fnames:
                if fname.endswith((".md", ".py", ".json", ".yaml", ".toml", ".txt")):
                    rel = os.path.relpath(os.path.join(root, fname), target)
                    contents.append(rel)
                    try:
                        with open(os.path.join(root, fname), encoding="utf-8") as f:
                            files[rel] = f.read()
                    except:
                        pass
        
        data = {
            "name": os.path.basename(target),
            "full_name": os.path.basename(target),
            "description": "本地技能目录",
            "stars": 0,
            "forks": 0,
            "language": "N/A",
            "topics": [],
            "files": files,
            "contents": contents,
        }
    
    print(f"[*] 仓库: {data['full_name']}")
    print(f"[*] 文件数: {len(data['contents'])}")
    print()
    
    # 执行审查
    print("[*] 正在执行 8 维审查...")
    result = review_skill(data)
    
    # 输出终端摘要
    print()
    print("=" * 50)
    print(f"  SKILL REVIEW REPORT")
    print(f"  {data['full_name']}")
    print("=" * 50)
    print()
    
    for dim in DIMENSIONS:
        s = result["scores"][dim["id"]]
        bar = "".join(["#" if i < int(s["score"]) else "-" for i in range(10)])
        print(f"  {dim['name_cn']:8s} [{bar}] {s['score']}/10")
    
    print()
    print(f"  >>> 总分: {result['total_score']}/10  评级: {result['rating']} <<<")
    print()
    
    if result["suggestions"]:
        print("  改进建议:")
        for i, sug in enumerate(result["suggestions"], 1):
            print(f"    {i}. {sug}")
    
    print()
    
    # 生成 HTML
    if args.html:
        html = generate_html(result)
        out_path = args.output
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] HTML 报告已保存: {out_path}")
    
    print("[OK] 审查完成")


if __name__ == "__main__":
    main()
