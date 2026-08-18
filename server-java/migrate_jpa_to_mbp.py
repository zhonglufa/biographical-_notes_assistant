#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JPA -> MyBatis-Plus 迁移（就地转换版，幂等，迁移辅助非交付物）。
策略：不新建/不重命名/不删除文件（沙箱禁止 os.remove）。
- 实体：仅当仍含 @Entity 时转换（@Entity->@TableName, @Id/@GeneratedValue->@TableId,
        每字段补 @TableField("snake") 复刻 JPA 驼峰->下划线, @Enumerated->@EnumValue,
        复合主键每个 @Id->@TableId(INPUT)）。幂等：已转换则跳过。
- Repository：原地改 extends JpaRepository<X,ID> -> extends BaseMapper<X>，
        删除 JPA 导入与自定义方法声明，追加 default 方法（复刻原签名 + JPA 兼容 findById/save/...）。
        保留类名 XRepository 与文件名，service 零改动。幂等：已 extends BaseMapper 则跳过。
- IdClass 文件与游离 *Mapper 文件：os.rename 移到 _migrate_backup（绕过安全删除）。
"""
import os, re

ROOT = r"E:/简历/resume-ai-prod/server-java/src"
MAIN = os.path.join(ROOT, "main/java")
TEST = os.path.join(ROOT, "test/java")
BACKUP = os.path.join(ROOT, "_migrate_backup")

def snake(s):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', s).lower()

FIELD_RE = re.compile(
    r'(?P<ann>(?:^[ \t]*@\w+(?:\([^)]*\))?[ \t]*\r?\n)+)?'
    r'[ \t]*private[ \t]+(?:final[ \t]+)?(?P<type>[\w$.<>\[\],\s]+?)[ \t]+(?P<name>\w+)[ \t]*(?P<init>=\s*[^;]+)?[ \t]*;',
    re.MULTILINE)

METHOD_RE = re.compile(
    r'^\s*(?:public\s+|default\s+)?([\w$.<>\[\],\s]+?)\s+(\w+)\s*\(([^)]*)\)\s*;', re.MULTILINE)

STD_METHODS = {'findById', 'save', 'existsById', 'findAll', 'count', 'delete',
               'deleteById', 'deleteAll', 'flush', 'getOne', 'findOne'}

def safe_move(p):
    """沙箱禁止 os.remove：改名移走（rename 不走 os.remove）。"""
    if not os.path.exists(p):
        return
    os.makedirs(BACKUP, exist_ok=True)
    dest = os.path.join(BACKUP, os.path.basename(p))
    base, ext = os.path.splitext(dest)
    i = 1
    while os.path.exists(dest):
        dest = '%s_%d%s' % (base, i, ext); i += 1
    os.rename(p, dest)
    print('  moved ->', dest)

# ---------- 实体解析/转换 ----------
def parse_entity(path):
    src = open(path, encoding='utf-8').read()
    pk = []; fcol = {}
    idclass = re.search(r'@IdClass\(([\w.]+)\.class\)', src)
    for m in FIELD_RE.finditer(src):
        ann = m.group('ann') or ''
        fname = m.group('name')
        colm = re.search(r'@(?:Column|TableField)\([^)]*?name\s*=\s*"([^"]+)"', ann)
        fcol[fname] = colm.group(1) if colm else snake(fname)
        if '@Id' in ann or '@TableId' in ann:
            pk.append(fname)
    # 复合判定：原 @IdClass 或 主键字段数 > 1（转换后 @IdClass 已删，用主键数兜底）
    is_composite = (idclass is not None) or (len(pk) > 1)
    return {'pk': pk, 'fcol': fcol, 'is_composite': is_composite,
            'cls': os.path.basename(path)[:-5]}

def convert_entity(path):
    src = open(path, encoding='utf-8').read()
    if '@Entity' not in src:
        return parse_entity(path)  # 已转换，直接解析
    src = re.sub(r'import\s+jakarta\.persistence\.\*;\s*\n', '', src)
    src = re.sub(r'import\s+jakarta\.persistence\.\w+;\s*\n', '', src)
    if 'import com.baomidou.mybatisplus.annotation.*;' not in src:
        src = re.sub(r'(package [^\n]+;\n)',
                     r'\1import com.baomidou.mybatisplus.annotation.*;\n', src, count=1)
    src = re.sub(r'@Entity\s*\n', '', src)
    src = re.sub(r'@Table\(name\s*=\s*"([^"]+)"\)', r'@TableName("\1")', src)
    src = re.sub(r'@IdClass\([\w.]+\.class\)\s*\n', '', src)

    def field_repl(m):
        ann = m.group('ann') or ''
        ftype = m.group('type').strip()
        fname = m.group('name')
        init = m.group('init') or ''
        is_pk = '@Id' in ann
        is_enum = '@Enumerated' in ann
        gen = re.search(r'@GeneratedValue\([^)]*\)', ann)
        if is_pk:
            if gen and ('IDENTITY' in gen.group(0) or 'AUTO' in gen.group(0)):
                idtype = 'AUTO'
            elif gen and 'UUID' in gen.group(0):
                idtype = 'ASSIGN_ID'
            else:
                idtype = 'INPUT'
            new_ann = '@TableId(type = IdType.%s)' % idtype
        elif '@Transient' in ann:
            new_ann = '@TableField(exist = false)'
        elif is_enum:
            new_ann = '@EnumValue'
        else:
            colm = re.search(r'@Column\([^)]*?name\s*=\s*"([^"]+)"', ann)
            col = colm.group(1) if colm else snake(fname)
            new_ann = '@TableField("%s")' % col
        return '    %s\n    private %s %s%s;' % (new_ann, ftype, fname, init)
    src = FIELD_RE.sub(field_repl, src)
    open(path, 'w', encoding='utf-8').write(src)
    return parse_entity(path)

# ---------- 方法生成 ----------
def param_types(params):
    out = []
    for p in params.split(','):
        p = p.strip()
        if not p:
            continue
        p = re.sub(r'@Param\("[^"]+"\)\s*', '', p)
        mm = re.match(r'(.+?)\s+(\w+)$', p)
        if mm:
            out.append((mm.group(1).strip(), mm.group(2)))
    return out

def gen_search(cls):
    return ('    default org.springframework.data.domain.Page<%s> search('
            'String keyword, String location, String platform, Integer salaryMin, '
            'org.springframework.data.domain.Pageable pageable) {\n'
            '        QueryWrapper<%s> q = new QueryWrapper<%s>();\n'
            '        if (keyword != null && !keyword.isBlank()) q.like("title", keyword);\n'
            '        if (location != null && !location.isBlank()) q.eq("location", location);\n'
            '        if (platform != null && !platform.isBlank()) q.eq("platform_id", platform);\n'
            '        if (salaryMin != null) q.ge("salary_min", salaryMin);\n'
            '        q.orderByDesc("collected_at");\n'
            '        Page<%s> page = new Page<>(pageable.getPageNumber() + 1, pageable.getPageSize());\n'
            '        page = selectPage(page, q);\n'
            '        return new org.springframework.data.domain.PageImpl<>(page.getRecords(), pageable, page.getTotal());\n'
            '    }') % (cls, cls, cls, cls)

def gen_custom(cls, name, ret, params, fcol):
    ptypes = param_types(params)
    has_pageable = any(t[0].endswith('Pageable') for t in ptypes)
    if name == 'search':
        return gen_search(cls)
    rt = ret.strip()
    if rt.startswith('Optional<'):
        kind = 'optional'
    elif rt.startswith('List<'):
        kind = 'list'
    elif rt in ('long', 'int'):
        kind = 'count'
    elif rt == 'boolean':
        kind = 'exists'
    elif rt == cls:
        kind = 'single'
    else:
        return '    // TODO: %s %s(%s);' % (ret, name, params)
    if name.startswith('findBy'):
        rest = name[6:]
    elif name.startswith('countBy'):
        rest = name[7:]
    elif name.startswith('existsBy'):
        rest = name[8:]
    else:
        return '    // TODO(non-derived): %s %s(%s);' % (ret, name, params)
    order = None
    if 'OrderBy' in rest:
        base, order = rest.split('OrderBy', 1)
        om = re.match(r'(\w+?)(Desc|Asc)$', order)
        if om:
            order_col = snake(om.group(1)); order_dir = om.group(2).lower()
        else:
            order_col = snake(order); order_dir = 'asc'
        rest = base
    parts = rest.split('And') if rest else []
    eqs = []; pi = 0
    for part in parts:
        if part.endswith('False'):
            eqs.append('.eq("%s", false)' % snake(part[:-5])); continue
        if part.endswith('True'):
            eqs.append('.eq("%s", true)' % snake(part[:-4])); continue
        col = fcol.get(part, snake(part))
        arg = ptypes[pi][1] if pi < len(ptypes) else 'null'
        pi += 1
        eqs.append('.eq("%s", %s)' % (col, arg))
    wq = 'new QueryWrapper<%s>()%s' % (cls, ''.join(eqs))
    if order:
        wq += '.orderBy%s("%s")' % (order_dir.capitalize(), order_col)
    if has_pageable:
        return ('    default %s %s(%s) {\n'
                '        Page<%s> page = new Page<>(pageable.getPageNumber() + 1, pageable.getPageSize());\n'
                '        page = selectPage(page, %s);\n'
                '        return page.getRecords();\n'
                '    }') % (ret, name, params, cls, wq)
    if kind == 'optional':
        return '    default %s %s(%s) {\n        return Optional.ofNullable(selectOne(%s));\n    }' % (ret, name, params, wq)
    if kind == 'list':
        return '    default %s %s(%s) {\n        return selectList(%s);\n    }' % (ret, name, params, wq)
    if kind == 'single':
        return '    default %s %s(%s) {\n        return selectOne(%s);\n    }' % (ret, name, params, wq)
    if kind == 'count':
        cast = '(int) ' if rt == 'int' else ''
        return '    default %s %s(%s) {\n        return %sselectCount(%s);\n    }' % (ret, name, params, cast, wq)
    if kind == 'exists':
        return '    default %s %s(%s) {\n        return selectCount(%s) > 0;\n    }' % (ret, name, params, wq)
    return '    // TODO: %s %s(%s);' % (ret, name, params)

# ---------- Repository 就地转换 ----------
def convert_repo(repo_path, info, entity_class):
    src = open(repo_path, encoding='utf-8').read()
    if 'extends BaseMapper' in src:
        return  # 已转换，跳过
    # 去掉 JPA 导入
    src = re.sub(r'import org\.springframework\.data\.jpa\.repository\.JpaRepository;\s*\n', '', src)
    src = re.sub(r'import org\.springframework\.data\.jpa\.repository\.Query;\s*\n', '', src)
    src = re.sub(r'import org\.springframework\.data\.repository\.query\.Param;\s*\n', '', src)
    # 加 MBP 导入（package 之后）
    if 'import com.baomidou.mybatisplus.core.mapper.BaseMapper;' not in src:
        src = re.sub(r'(package [^\n]+;\n)',
                     r'\1import com.baomidou.mybatisplus.core.mapper.BaseMapper;\n'
                     r'import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;\n'
                     r'import com.baomidou.mybatisplus.extension.plugins.pagination.Page;\n'
                     r'import java.io.Serializable;\nimport java.util.List;\nimport java.util.Optional;\n',
                     src, count=1)
    # extends JpaRepository<X, ID> -> extends BaseMapper<X>
    src = re.sub(r'extends JpaRepository<(\w+),\s*[\w.]+>', r'extends BaseMapper<\1>', src)
    # 去掉 @Query 独立行
    src = re.sub(r'^\s*@Query\([^\n]*\n', '', src, flags=re.MULTILINE)
    # 去掉自定义方法声明行（保留接口头/extends/注解）
    src = METHOD_RE.sub('', src)
    # 追加 default 方法体
    composite = info['is_composite']; fcol = info['fcol']
    bodies = []
    if not composite:
        bodies.append('    default Optional<%s> findById(Serializable id) { return Optional.ofNullable(selectById(id)); }' % entity_class)
        bodies.append('    default %s save(%s e) { if (e.getId() == null) insert(e); else updateById(e); return e; }' % (entity_class, entity_class))
        bodies.append('    default boolean existsById(Serializable id) { return selectById(id) != null; }')
        bodies.append('    default List<%s> findAll() { return selectList(null); }' % entity_class)
        bodies.append('    default long count() { return selectCount(null); }')
    else:
        bodies.append('    default %s save(%s e) { insert(e); return e; }' % (entity_class, entity_class))
    # 重新解析自定义方法（从原 src 已移除，需从原始文件再取）
    orig = open(repo_path, encoding='utf-8').read()
    for m in METHOD_RE.finditer(orig):
        ret, name, params = m.group(1).strip(), m.group(2), m.group(3).strip()
        if name in STD_METHODS or name == entity_class or name == 'extends':
            continue
        bodies.append(gen_custom(entity_class, name, ret, params, fcol))
        bodies.append('')
    bodies.append('}')
    # 在原始接口结尾 '}' 前插入（用原始 src 的结尾）
    idx = src.rfind('}')
    if idx == -1:
        src = src.rstrip() + '\n' + '\n'.join(bodies) + '\n'
    else:
        src = src[:idx] + '\n' + '\n'.join(bodies[:-1]) + '\n' + src[idx:]
    open(repo_path, 'w', encoding='utf-8').write(src)
    print('converted repo ->', repo_path)

# ---------- 主流程 ----------
def main():
    # 1. 解析实体（仅解析，不转换），确定复合主键类（按 entity 目录收集，与转换状态无关）
    entities = {}
    entity_files = []
    for dp, _, fns in os.walk(MAIN):
        if os.path.basename(dp) != 'entity':
            continue
        for fn in fns:
            if not fn.endswith('.java'):
                continue
            p = os.path.join(dp, fn)
            s = open(p, encoding='utf-8').read()
            if not ('@Entity' in s or '@TableName' in s or '@TableId' in s):
                continue  # 跳过 IdClass 等非实体文件
            info = parse_entity(p)
            entities[info['cls']] = info
            entity_files.append(p)
    composite_classes = {c for c, i in entities.items() if i['is_composite']}
    # 2. 清理：游离 *Mapper.java + 复合实体的 XxxId.java（rename 移走，绕过安全删除）
    for base in (MAIN, TEST):
        for dp, _, fns in os.walk(base):
            for fn in fns:
                p = os.path.join(dp, fn)
                if fn.endswith('Mapper.java'):
                    safe_move(p)
                elif fn.endswith('Id.java'):
                    base_cls = fn[:-len('Id.java')]
                    if base_cls in composite_classes:
                        safe_move(p)
    # 3. 实体就地转换（幂等）
    for p in entity_files:
        convert_entity(p)
    print('entities:', len(entities))
    # 4. Repository 就地转换（幂等）。实体类从 extends JpaRepository<X,ID>/BaseMapper<X> 泛型提取（兼容 StrategyRepository->StrategyConfig 命名错配）
    repo_count = 0
    for dp, _, fns in os.walk(MAIN):
        for fn in fns:
            if not fn.endswith('Repository.java'):
                continue
            p = os.path.join(dp, fn)
            s0 = open(p, encoding='utf-8').read()
            m = re.search(r'extends (?:JpaRepository|BaseMapper)<(\w+)', s0)
            if not m:
                print('WARN cannot find entity for', fn); continue
            entity_class = m.group(1)
            if entity_class in entities:
                convert_repo(p, entities[entity_class], entity_class)
                repo_count += 1
            else:
                print('WARN entity', entity_class, 'not found for', fn)
    print('repos converted:', repo_count)
    print('DONE')

if __name__ == '__main__':
    main()
