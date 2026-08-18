package com.resumeai.module.strategy;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.resumeai.common.BizException;
import com.resumeai.module.strategy.dto.StrategiesRequest;
import com.resumeai.module.strategy.dto.StrategiesResponse;
import com.resumeai.module.strategy.entity.StrategyConfig;
import com.resumeai.module.strategy.repository.StrategyRepository;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 策略配置业务实现（A12/A13 · 对齐 LLD-策略配置模块 §2/§5）。
 *
 * <p>防生产事故约束：
 * <ul>
 *   <li>字段级校验：{@code matchThreshold} ∈ [0,1]，越界 400（契约 additionalProperties:false + range）；</li>
 *   <li>LWW：写时整体覆盖（带 updatedAt 时间戳），不静默合并（HLD §1206）；</li>
 *   <li>默认值兜底：无记录读返回默认（非 500），避免前端空指针。</li>
 * </ul>
 */
@Service
public class StrategyServiceImpl implements StrategyService {

    private static final double DEFAULT_MATCH_THRESHOLD = 0.60;
    private static final int DEFAULT_DAILY_LIMIT = 30;

    private final StrategyRepository repo;
    private final ObjectMapper mapper = new ObjectMapper();

    public StrategyServiceImpl(StrategyRepository repo) {
        this.repo = repo;
    }

    @Override
    public StrategiesResponse get(String userId) {
        StrategyConfig cfg = repo.findByUserId(userId).orElse(null);
        if (cfg == null) {
            return new StrategiesResponse(DEFAULT_MATCH_THRESHOLD, DEFAULT_DAILY_LIMIT,
                    new ArrayList<>(), new ArrayList<>());
        }
        return new StrategiesResponse(cfg.getMatchThreshold(), cfg.getDailyLimit(),
                fromJson(cfg.getPlatformsJson()), fromJson(cfg.getBlacklistJson()));
    }

    @Override
    public StrategiesResponse save(String userId, StrategiesRequest req) {
        if (req.matchThreshold() < 0 || req.matchThreshold() > 1) {
            throw new BizException(400, "INVALID_MATCH_THRESHOLD");
        }
        StrategyConfig cfg = repo.findByUserId(userId).orElse(new StrategyConfig());
        cfg.setUserId(userId);
        cfg.setMatchThreshold(req.matchThreshold());
        cfg.setDailyLimit(req.dailyLimit());
        cfg.setPlatformsJson(toJson(req.platforms()));
        cfg.setBlacklistJson(toJson(req.blacklist()));
        cfg.setUpdatedAt(System.currentTimeMillis());
        repo.save(cfg);
        return new StrategiesResponse(cfg.getMatchThreshold(), cfg.getDailyLimit(),
                fromJson(cfg.getPlatformsJson()), fromJson(cfg.getBlacklistJson()));
    }

    private String toJson(List<String> list) {
        try {
            return mapper.writeValueAsString(list == null ? new ArrayList<>() : list);
        } catch (Exception e) {
            throw new BizException(500, "JSON_SERIALIZE_ERROR");
        }
    }

    private List<String> fromJson(String json) {
        if (json == null || json.isBlank()) {
            return new ArrayList<>();
        }
        try {
            return mapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            return new ArrayList<>();
        }
    }
}
