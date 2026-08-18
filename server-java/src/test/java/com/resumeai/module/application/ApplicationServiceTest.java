package com.resumeai.module.application;

import com.resumeai.common.BizException;
import com.resumeai.module.application.dto.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 投递模块集成测试（@SpringBootTest + H2 内存库 · test profile）。
 * 覆盖：A09 双层幂等(请求级409)/限流(≤50)/A11 详情时间线/数据隔离(404)。
 * 注意：不验证业务四元组防重投（需 P1 job 模块提供真实 platform_id，已在 Service 标注 TODO）。
 */
@SpringBootTest
@ActiveProfiles("test")
@Transactional
class ApplicationServiceTest {

    @Autowired
    private ApplicationService svc;

    @Test
    void 批量投递_accepted计数正确() {
        ApplyBatchResponse resp = svc.applyBatch("u-test", new ApplyBatchRequest(List.of("job1", "job2"), null, "req-uuid-1"));
        assertEquals(2, resp.accepted());
        assertEquals(0, resp.rejected().size());
    }

    @Test
    void 请求级幂等_重复提交抛409() {
        svc.applyBatch("u-test", new ApplyBatchRequest(List.of("jobA"), null, "req-dup-key"));
        BizException ex = assertThrows(BizException.class,
                () -> svc.applyBatch("u-test", new ApplyBatchRequest(List.of("jobA"), null, "req-dup-key")));
        assertEquals(409, ex.getCode());
    }

    @Test
    void 空jobIds_抛400() {
        assertThrows(BizException.class,
                () -> svc.applyBatch("u-test", new ApplyBatchRequest(List.of(), null, "req-empty")));
    }

    @Test
    void 超50_抛400() {
        List<String> many = new ArrayList<>();
        for (int i = 0; i < 51; i++) {
            many.add("job" + i);
        }
        assertThrows(BizException.class,
                () -> svc.applyBatch("u-test", new ApplyBatchRequest(many, null, "req-toomany")));
    }

    @Test
    void 详情_含pending_confirm时间线() {
        svc.applyBatch("u-detail", new ApplyBatchRequest(List.of("jx"), null, "req-detail"));
        ApplicationsListResponse list = svc.list("u-detail");
        assertEquals(1, list.items().size());
        ApplicationDetailResponse d = svc.detail("u-detail", list.items().get(0).id());
        assertEquals("pending_confirm", d.status());
        assertEquals(1, d.timeline().size());
        assertNull(d.timeline().get(0).from());
    }

    @Test
    void 他人数据_详情返回404不泄露归属() {
        svc.applyBatch("u-owner", new ApplyBatchRequest(List.of("secret"), null, "req-owner"));
        String id = svc.list("u-owner").items().get(0).id();
        assertThrows(BizException.class, () -> svc.detail("u-stranger", id));
    }
}
