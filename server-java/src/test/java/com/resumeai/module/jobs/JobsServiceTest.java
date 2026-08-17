package com.resumeai.module.jobs;

import com.resumeai.common.BizException;
import com.resumeai.module.jobs.dto.FavoriteRequest;
import com.resumeai.module.jobs.dto.FavoriteResponse;
import com.resumeai.module.jobs.dto.JobStub;
import com.resumeai.module.jobs.dto.JobsListResponse;
import com.resumeai.module.jobs.entity.Job;
import com.resumeai.module.jobs.entity.JobFavorite;
import com.resumeai.module.jobs.entity.JobMatch;
import com.resumeai.module.jobs.repository.JobFavoriteRepository;
import com.resumeai.module.jobs.repository.JobMatchRepository;
import com.resumeai.module.jobs.repository.JobRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** A07 / A08 关键路径单测（H2 内存库 · 对齐 ApplicationServiceTest 范式）。 */
@SpringBootTest
class JobsServiceTest {

    @Autowired
    private JobRepository jobRepo;
    @Autowired
    private JobMatchRepository matchRepo;
    @Autowired
    private JobFavoriteRepository favRepo;
    @Autowired
    private JobsService svc;

    private Job newJob(String title, String company, String platform, long collectedAt) {
        Job j = new Job();
        j.setPlatformId(platform);
        j.setTitle(title);
        j.setCompany(company);
        j.setSource("search");
        j.setCollectedAt(collectedAt);
        j.setSalaryMin(10000);
        return jobRepo.save(j);
    }

    @Test
    void search_returnsJobsWithMatchAndFavorite() {
        Job j1 = newJob("Java工程师", "A公司", "boss", 200L);
        Job j2 = newJob("前端工程师", "B公司", "liepin", 100L);

        JobMatch m = new JobMatch();
        m.setUserId("u-1");
        m.setJobId(j1.getId());
        m.setScore(85);
        m.setBand("green");
        m.setReason("技能高度匹配");
        m.setComputedAt(100L);
        matchRepo.save(m);

        JobFavorite f = new JobFavorite();
        f.setUserId("u-1");
        f.setJobId(j1.getId());
        f.setAction("favorite");
        f.setCreatedAt(100L);
        favRepo.save(f);

        JobsListResponse res = svc.search("u-1", null, null, null, null, 1, 20);
        assertEquals(2, res.items().size());
        assertEquals(2, res.total());

        Optional<JobStub> stub1 = res.items().stream()
                .filter(s -> "Java工程师".equals(s.title())).findFirst();
        assertTrue(stub1.isPresent());
        assertEquals(Integer.valueOf(85), stub1.get().matchScore());
        assertEquals("green", stub1.get().matchBand());
        assertEquals(Boolean.TRUE, stub1.get().favorited());
    }

    @Test
    void favorite_favoritesThenIdempotentThenIgnore() {
        Job j = newJob("测试岗", "C公司", "zhaopin", 300L);

        FavoriteResponse r1 = svc.favorite("u-9", String.valueOf(j.getId()), new FavoriteRequest("favorite"));
        assertEquals("favorited", r1.status());
        assertEquals(String.valueOf(j.getId()), r1.favoriteId());

        // 幂等：重复 favorite 无副作用
        FavoriteResponse r2 = svc.favorite("u-9", String.valueOf(j.getId()), new FavoriteRequest("favorite"));
        assertEquals("favorited", r2.status());

        FavoriteResponse r3 = svc.favorite("u-9", String.valueOf(j.getId()), new FavoriteRequest("ignore"));
        assertEquals("ignored", r3.status());
        assertEquals(null, r3.favoriteId());
    }

    @Test
    void favorite_notFound_throws404() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.favorite("u-1", "999999", new FavoriteRequest("favorite")));
        assertEquals(404, ex.getCode());
    }

    @Test
    void favorite_invalidAction_throws400() {
        Job j = newJob("非法动作岗", "D公司", "51job", 400L);
        BizException ex = assertThrows(BizException.class,
                () -> svc.favorite("u-1", String.valueOf(j.getId()), new FavoriteRequest("bogus")));
        assertEquals(400, ex.getCode());
    }
}
