import os
import re
import yaml
from typing import List,Dict,Any
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent.parent/"skills"

_skills_meta_cache:List[Dict[str,Any]] | None = None


#这个函数主要是用于先把skill.md的所有内容拿到手
def _parse_skill_md(file_path:Path) ->Dict[str,Any]:
    """解析SKILL.md文件,提取YAML frontmatter和正文内容"""
    with open(file_path,"r",encoding="utf-8")as f:
        content = f.read()
    match = re.match(r"^---\n(.*?)\n---(.*)$",content,re.DOTALL)
    if not match:
        raise ValueError(f"{file_path}下的文件缺少元数据")

    frontmatter_text = match.group(1)
    body = match.group(2).strip()

    #获取到yaml格式文件中的内容 转化为字典
    frontmatter = yaml.safe_load(frontmatter_text)

    return {
        "name":frontmatter.get("name"),
        "description":frontmatter.get("description"),
        "version":frontmatter.get("version","1.0.0"),
        "tools_required":frontmatter.get("tools_required",[]),
        "body":body,
        "path":str(file_path),
    }

def scan_skills() ->List[Dict[str,Any]]:
    """扫描skill目录,只拿元数据"""
    if not SKILLS_DIR.exists():
        return []

    skills = []
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir /"SKILL.md"
        if not skill_md.exists():
            continue
        try:
            meta = _parse_skill_md(skill_md)
            skills.append({
                "name":meta["name"],
                "description":meta["description"],
                "version":meta["version"],
                "tools_required":meta["tools_required"]
            })
        except Exception as e:
            print(f"[SKILL] 加载技能{skill_dir.name}失败 :{e}")
    return skills


def get_all_skills_meta() ->List[Dict[str,Any]]:
    """获取所有技能元数据,主要是进行缓存"""
    global _skills_meta_cache
    if _skills_meta_cache is None:
        _skills_meta_cache  = scan_skills()
    return _skills_meta_cache

def load_skill_content(skill_name:str) ->str:
    """根据技能名称返回完整的skill.md的正文"""
    skills_dir = SKILLS_DIR
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            meta = _parse_skill_md(skill_md)
            if meta["name"] == skill_name:
                return meta["body"]
        except:
            continue
    raise ValueError(f"Skill {skill_name} 没找到")


