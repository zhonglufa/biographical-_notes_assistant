package com.resumeai.module.strategy;

import com.resumeai.module.strategy.dto.StrategiesRequest;
import com.resumeai.module.strategy.dto.StrategiesResponse;

/**
 * 策略配置服务接口（A12 读 / A13 写）。
 */
public interface StrategyService {

    /** A12 读取当前用户生效策略；无记录返回默认值（matchThreshold=0.60, dailyLimit=30, 空列表）。 */
    StrategiesResponse get(String userId);

    /** A13 保存（upsert）当前用户策略；冲突以 PC 为准 LWW（HLD §1206）。 */
    StrategiesResponse save(String userId, StrategiesRequest req);
}
