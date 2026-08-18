package com.resumeai.module.resume;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.resumeai.common.BizException;
import com.resumeai.module.resume.dto.AtsScoreRequest;
import com.resumeai.module.resume.dto.AtsScoreResponse;
import com.resumeai.module.resume.dto.ResumeCreateRequest;
import com.resumeai.module.resume.dto.ResumeCreateResponse;
import com.resumeai.module.resume.dto.ResumeDiffChange;
import com.resumeai.module.resume.dto.ResumeDiffRequest;
import com.resumeai.module.resume.dto.ResumeDiffResponse;
import com.resumeai.module.resume.dto.ResumeVersionItem;
import com.resumeai.module.resume.dto.ResumeVersionsResponse;
import com.resumeai.module.resume.entity.Resume;
import com.resumeai.module.resume.entity.ResumeVersion;
import com.resumeai.module.resume.repository.ResumeRepository;
import com.resumeai.module.resume.repository.ResumeVersionRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * 简历工作台业务实现（A04 / A05 / A06 · 对齐 LLD-简历工作台模块）。
 *
 * <p>防生产事故约束：
 * <ul>
 *   <li>不调 LLM 润色（交 Python B04）、不管理模板 CSS（前端）；只做资产存取 / diff / ATS 触发；</li>
 *   <li>数据隔离：所有读写按 user_id 归属，越权返回 404；</li>
 *   <li>快照不可变：每次创建新版本（version_no 递增），投递锁定当时版本；</li>
 *   <li>A06 异步：锁版本返回 taskId+pending，真实评分经 B05（TODO 接 AI 编排）。</li>
 * </ul>
 */
@Service
public class ResumeServiceImpl implements ResumeService {

    private final ResumeRepository resumeRepo;
    private final ResumeVersionRepository versionRepo;
    private final ObjectMapper mapper = new ObjectMapper();

    public ResumeServiceImpl(ResumeRepository resumeRepo, ResumeVersionRepository versionRepo) {
        this.resumeRepo = resumeRepo;
        this.versionRepo = versionRepo;
    }

    @Override
    public ResumeCreateResponse create(String userId, ResumeCreateRequest req) {
        if (req.title() == null || req.title().isBlank()) {
            throw new BizException(400, "INVALID_PARAM");
        }
        String snapshot;
        try {
            snapshot = mapper.writeValueAsString(req.content() == null ? new Object() : req.content());
        } catch (Exception e) {
            throw new BizException(400, "RESUME_CONTENT_INVALID");
        }

        long now = System.currentTimeMillis();
        Resume resume = new Resume();
        resume.setUserId(userId);
        resume.setTitle(req.title());
        resume.setCreatedAt(now);
        resume.setUpdatedAt(now);
        resume = resumeRepo.save(resume);

        ResumeVersion v = new ResumeVersion();
        v.setResumeId(resume.getId());
        v.setUserId(userId);
        v.setVersionNo(1);
        v.setSnapshot(snapshot);
        v.setEncrypted(true);
        v.setCreatedAt(now);
        v = versionRepo.save(v);

        resume.setPreferredVersionId(v.getId());
        resumeRepo.save(resume);

        return new ResumeCreateResponse(String.valueOf(resume.getId()), String.valueOf(v.getId()), now);
    }

    @Override
    public ResumeVersionsResponse listVersions(String userId, String resumeId) {
        Long rid = parseId(resumeId, "RESOURCE_NOT_FOUND");
        Resume resume = resumeRepo.findByUserIdAndId(userId, rid).orElse(null);
        if (resume == null) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        List<ResumeVersion> versions = versionRepo.findByResumeIdOrderByVersionNoAsc(rid);
        List<ResumeVersionItem> items = new ArrayList<>();
        for (ResumeVersion v : versions) {
            items.add(new ResumeVersionItem(
                    String.valueOf(v.getId()),
                    v.getVersionNo(),
                    v.getCreatedAt(),
                    null,
                    v.getId().equals(resume.getPreferredVersionId())));
        }
        return new ResumeVersionsResponse(items, versions.size() >= 2);
    }

    @Override
    public ResumeDiffResponse diff(String userId, String resumeId, ResumeDiffRequest req) {
        Long rid = parseId(resumeId, "RESOURCE_NOT_FOUND");
        if (resumeRepo.findByUserIdAndId(userId, rid).isEmpty()) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        ResumeVersion from = versionRepo.findByResumeIdAndId(rid, parseId(req.fromVersionId(), "INVALID_PARAM")).orElse(null);
        ResumeVersion to = versionRepo.findByResumeIdAndId(rid, parseId(req.toVersionId(), "INVALID_PARAM")).orElse(null);
        if (from == null || to == null) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        Object a = readJson(from.getSnapshot());
        Object b = readJson(to.getSnapshot());
        List<ResumeDiffChange> changes = new ArrayList<>();
        diffJson(a, b, null, changes);
        return new ResumeDiffResponse(changes, System.currentTimeMillis());
    }

    @Override
    public AtsScoreResponse atsScore(String userId, AtsScoreRequest req) {
        Long vid = parseId(req.resumeVersionId(), "INVALID_PARAM");
        if (versionRepo.findByUserIdAndId(userId, vid).isEmpty()) {
            throw new BizException(404, "RESOURCE_NOT_FOUND");
        }
        // 异步触发：锁版本返回 taskId + pending；真实评分经 B05（TODO 接 AI 编排服务，结果回填 ats_report）。
        String taskId = "ats-task-" + vid + "-" + System.currentTimeMillis();
        return new AtsScoreResponse(taskId, "pending");
    }

    private Long parseId(String s, String code) {
        try {
            return Long.valueOf(s);
        } catch (NumberFormatException e) {
            throw new BizException(404, code);
        }
    }

    private Object readJson(String json) {
        if (json == null) {
            return null;
        }
        try {
            Object parsed = mapper.readValue(json, new TypeReference<Object>() {});
            // H2 的 JSON 列在 JDBC getString() 时可能把 JSON 文本作为「JSON 字符串字面量」返回
            // （外层带引号），Jackson 会把它反序列化成 Java String 而非 Map/List。
            // 此时再解析一层，得到真正的结构化对象，保证跨库（H2/MySQL/PG）行为一致。
            if (parsed instanceof String s) {
                return mapper.readValue(s, new TypeReference<Object>() {});
            }
            return parsed;
        } catch (Exception e) {
            return json;
        }
    }

    /** 递归字段级 diff：section→field 路径为 key；缺失/新增/值变更分别标 removed/added/modified。 */
    @SuppressWarnings("unchecked")
    private void diffJson(Object a, Object b, String path, List<ResumeDiffChange> out) {
        if (a == null && b == null) {
            return;
        }
        if (a == null) {
            out.add(new ResumeDiffChange(path, "added", null, str(b)));
            return;
        }
        if (b == null) {
            out.add(new ResumeDiffChange(path, "removed", str(a), null));
            return;
        }
        if (a instanceof Map && b instanceof Map) {
            Map<String, Object> ma = (Map<String, Object>) a;
            Map<String, Object> mb = (Map<String, Object>) b;
            Set<String> keys = new LinkedHashSet<>();
            keys.addAll(ma.keySet());
            keys.addAll(mb.keySet());
            for (String k : keys) {
                diffJson(ma.get(k), mb.get(k), path == null ? k : path + "." + k, out);
            }
            return;
        }
        if (!a.equals(b)) {
            out.add(new ResumeDiffChange(path, "modified", str(a), str(b)));
        }
    }

    private String str(Object o) {
        if (o == null) {
            return null;
        }
        if (o instanceof String) {
            return (String) o;
        }
        try {
            return mapper.writeValueAsString(o);
        } catch (Exception e) {
            return String.valueOf(o);
        }
    }
}
