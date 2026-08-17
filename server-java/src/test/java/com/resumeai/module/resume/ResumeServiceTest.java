package com.resumeai.module.resume;

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
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** A04 / A05 / A06 关键路径单测（H2 内存库）。 */
@SpringBootTest
class ResumeServiceTest {

    @Autowired
    private ResumeRepository resumeRepo;
    @Autowired
    private ResumeVersionRepository versionRepo;
    @Autowired
    private ResumeService svc;

    private ResumeCreateResponse createResume(String userId, String title) {
        Map<String, Object> content = new LinkedHashMap<>();
        content.put("name", "张三");
        content.put("skills", List.of("Java", "Spring"));
        return svc.create(userId, new ResumeCreateRequest(title, content, null));
    }

    @Test
    void create_storesResumeAndFirstVersion() {
        ResumeCreateResponse r = createResume("u-1", "后端工程师简历");
        assertEquals("后端工程师简历", resumeRepo.findById(Long.valueOf(r.resumeId())).orElseThrow().getTitle());
        List<ResumeVersion> versions = versionRepo.findByResumeIdOrderByVersionNoAsc(Long.valueOf(r.resumeId()));
        assertEquals(1, versions.size());
        assertEquals(1, versions.get(0).getVersionNo());
        assertEquals(r.versionId(), String.valueOf(versions.get(0).getId()));
    }

    @Test
    void create_emptyTitle_throws400() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.create("u-1", new ResumeCreateRequest("  ", Map.of(), null)));
        assertEquals(400, ex.getCode());
    }

    @Test
    void listVersions_diffAvailableWhenTwoVersions() {
        ResumeCreateResponse r = createResume("u-1", "简历A");
        // 人工再插一个版本以凑齐 2 版
        ResumeVersion v2 = new ResumeVersion();
        v2.setResumeId(Long.valueOf(r.resumeId()));
        v2.setUserId("u-1");
        v2.setVersionNo(2);
        v2.setSnapshot("{\"name\":\"张三\"}");
        v2.setEncrypted(true);
        v2.setCreatedAt(200L);
        versionRepo.save(v2);

        ResumeVersionsResponse res = svc.listVersions("u-1", r.resumeId());
        assertEquals(2, res.versions().size());
        assertTrue(res.diffAvailable());
        ResumeVersionItem preferred = res.versions().stream()
                .filter(ResumeVersionItem::isPreferred).findFirst().orElseThrow();
        assertEquals(r.versionId(), preferred.versionId());
    }

    @Test
    void listVersions_otherUser_404() {
        ResumeCreateResponse r = createResume("u-1", "简历B");
        BizException ex = assertThrows(BizException.class, () -> svc.listVersions("u-2", r.resumeId()));
        assertEquals(404, ex.getCode());
    }

    @Test
    void diff_detectsModifiedAndAddedField() {
        ResumeCreateResponse r = createResume("u-1", "简历C");
        Long rid = Long.valueOf(r.resumeId());

        ResumeVersion v1 = versionRepo.findByResumeIdAndId(rid, Long.valueOf(r.versionId())).orElseThrow();
        // v1 snapshot: {name:张三, skills:[Java,Spring]}

        ResumeVersion v2 = new ResumeVersion();
        v2.setResumeId(rid);
        v2.setUserId("u-1");
        v2.setVersionNo(2);
        Map<String, Object> c2 = new LinkedHashMap<>();
        c2.put("name", "张三丰"); // modified
        c2.put("skills", List.of("Java", "Spring")); // unchanged
        c2.put("title", "高级工程师"); // added
        try {
            v2.setSnapshot(new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(c2));
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
        v2.setEncrypted(true);
        v2.setCreatedAt(300L);
        versionRepo.save(v2);

        ResumeDiffResponse diff = svc.diff("u-1", r.resumeId(),
                new ResumeDiffRequest(r.versionId(), String.valueOf(v2.getId())));
        assertFalse(diff.changes().isEmpty());
        Optional<ResumeDiffChange> modified = diff.changes().stream()
                .filter(c -> "name".equals(c.field()) && "modified".equals(c.op())).findFirst();
        assertTrue(modified.isPresent());
        Optional<ResumeDiffChange> added = diff.changes().stream()
                .filter(c -> "title".equals(c.field()) && "added".equals(c.op())).findFirst();
        assertTrue(added.isPresent());
    }

    @Test
    void atsScore_returnsPendingTask() {
        ResumeCreateResponse r = createResume("u-1", "简历D");
        AtsScoreResponse ats = svc.atsScore("u-1", new AtsScoreRequest(r.versionId()));
        assertTrue(ats.taskId().startsWith("ats-task-"));
        assertEquals("pending", ats.status());
    }

    @Test
    void atsScore_unknownVersion_404() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.atsScore("u-1", new AtsScoreRequest("999999")));
        assertEquals(404, ex.getCode());
    }
}
