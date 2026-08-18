package com.resumeai.module.strategy;

import com.resumeai.common.BizException;
import com.resumeai.module.strategy.dto.StrategiesRequest;
import com.resumeai.module.strategy.dto.StrategiesResponse;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 策略配置集成测试（@SpringBootTest + H2 内存库 · test profile）。
 * 覆盖：A12 默认值兜底 / A13 保存-读取一致 / LWW 覆盖 / 阈值越界 400。
 */
@SpringBootTest
@ActiveProfiles("test")
class StrategyServiceTest {

    @Autowired
    private StrategyService svc;

    @Test
    void 默认策略_无记录时返回默认值() {
        StrategiesResponse r = svc.get("u-default");
        assertEquals(0.60, r.matchThreshold(), 0.001);
        assertEquals(30, r.dailyLimit());
        assertTrue(r.platforms().isEmpty());
        assertTrue(r.blacklist().isEmpty());
    }

    @Test
    void 保存后读取一致() {
        StrategiesRequest req = new StrategiesRequest(0.75, 50, List.of("boss", "lagou"), List.of("spam-co"));
        svc.save("u-save", req);
        StrategiesResponse r = svc.get("u-save");
        assertEquals(0.75, r.matchThreshold(), 0.001);
        assertEquals(50, r.dailyLimit());
        assertEquals(List.of("boss", "lagou"), r.platforms());
        assertEquals(List.of("spam-co"), r.blacklist());
    }

    @Test
    void 更新覆盖旧值_LWW() {
        svc.save("u-upd", new StrategiesRequest(0.5, 10, List.of("a"), List.of()));
        svc.save("u-upd", new StrategiesRequest(0.9, 99, List.of("b", "c"), List.of("x")));
        StrategiesResponse r = svc.get("u-upd");
        assertEquals(0.9, r.matchThreshold(), 0.001);
        assertEquals(99, r.dailyLimit());
        assertEquals(List.of("b", "c"), r.platforms());
        assertEquals(List.of("x"), r.blacklist());
    }

    @Test
    void 非法阈值_抛400() {
        BizException ex = assertThrows(BizException.class,
                () -> svc.save("u-bad", new StrategiesRequest(1.5, 10, List.of(), List.of())));
        assertEquals(400, ex.getCode());
    }
}
