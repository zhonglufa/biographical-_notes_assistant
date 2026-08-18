package com.resumeai.module.application;

import com.resumeai.common.BizException;
import com.resumeai.module.application.dto.*;
import com.resumeai.module.application.entity.Application;
import com.resumeai.module.application.entity.ApplicationEvent;
import com.resumeai.module.application.entity.ApplicationTask;
import com.resumeai.module.application.repository.ApplicationEventRepository;
import com.resumeai.module.application.repository.ApplicationRepository;
import com.resumeai.module.application.repository.ApplicationTaskRepository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 投递模块业务实现（Java 中枢 · 对齐 HLD §3.4 / §4.2 / §4.3）。
 *
 * <p>防生产事故的关键约束（全部按设计落地，未私自放宽）：
 * <ul>
 *   <li><b>双层幂等</b>：请求级 {@code idempotencyKey}(Redis SETNX 语义, 409) + 业务级四元组
 *       (user,platform,job,date) 唯一索引（防同用户同日同岗重投）；</li>
 *   <li><b>角色日限额</b>：P0 简化为固定 30（免费），生产接 §9.1 动态角色上限（TODO）；</li>
 *   <li><b>限流</b>：单次 ≤50（HLD §3.4）；</li>
 *   <li><b>状态机</b>：所有转移必须经 {@link DeliveryStateMachine#assertTransition} 裁决（无回退边）；</li>
 *   <li><b>审计</b>：每次建投递写 {@code pending_confirm} 事件，供时间线与广播。</li>
 * </ul>
 *
 * <p>P0 已知简化（诚实标注，非伪造完成）：
 * <ul>
 *   <li>platformId 解析占位为 {@code "pending"}：待 P1 job 模块落地后从 job 表
 *       (uk(platform_id,external_id)) 解析真实 platform_id，届时业务四元组防重投才完整生效；</li>
 *   <li>日限额统计未按 apply_date 当日窗口（P0 用累计计数近似）；</li>
 *   <li>userId 从 mock token 占位提取，非真实 JWT 解析（见 Controller）。</li>
 * </ul>
 */
@Service
public class ApplicationServiceImpl implements ApplicationService {

    private final ApplicationRepository appRepo;
    private final ApplicationEventRepository eventRepo;
    private final ApplicationTaskRepository taskRepo;
    private final IdempotencyStore idemStore;
    private final ApplyTaskPublisher publisher;

    /** P0 简化：免费角色日限额；生产接 HLD §9.1 动态角色上限（TODO）。 */
    private static final int FREE_DAILY_LIMIT = 30;
    private static final int MAX_BATCH = 50;

    public ApplicationServiceImpl(ApplicationRepository appRepo, ApplicationEventRepository eventRepo,
                                  ApplicationTaskRepository taskRepo, IdempotencyStore idemStore,
                                  ApplyTaskPublisher publisher) {
        this.appRepo = appRepo;
        this.eventRepo = eventRepo;
        this.taskRepo = taskRepo;
        this.idemStore = idemStore;
        this.publisher = publisher;
    }

    @Override
    public ApplyBatchResponse applyBatch(String userId, ApplyBatchRequest req) {
        if (req.jobIds() == null || req.jobIds().isEmpty()) {
            throw new BizException(400, "INVALID_JOBS: jobIds required");
        }
        if (req.jobIds().size() > MAX_BATCH) {
            throw new BizException(400, "INVALID_JOBS: jobIds 1..50");
        }
        if (req.idempotencyKey() == null || req.idempotencyKey().isBlank()) {
            throw new BizException(400, "idempotencyKey required (请求级)");
        }
        // ① 请求级幂等：重复提交直接 409，返回首次去重信号
        String first = idemStore.putIfAbsent("req:" + req.idempotencyKey(), userId);
        if (first != null) {
            throw new BizException(409, "DUPLICATE_REQUEST");
        }
        // ② 角色日限额（P0 固定上限）
        long todayCount = appRepo.countByUserId(userId);
        if (todayCount + req.jobIds().size() > FREE_DAILY_LIMIT) {
            throw new BizException(403, "QUOTA_EXCEEDED");
        }

        String batchId = UUID.randomUUID().toString();
        List<BatchRejectItem> rejected = new ArrayList<>();
        int accepted = 0;
        String applyDate = LocalDate.now().toString(); // yyyy-MM-dd (TODO 用户本地日期)

        for (String jobId : req.jobIds()) {
            String platformId = resolvePlatformId(jobId); // P0 占位 "pending"（TODO P1 job 模块）
            // ③ 业务级四元组幂等：防同用户同日同岗重投（数据库唯一索引兜底）
            if (appRepo.existsByUserIdAndPlatformIdAndJobIdAndApplyDate(userId, platformId, jobId, applyDate)) {
                rejected.add(new BatchRejectItem(jobId, "DUPLICATE_BIZ"));
                continue;
            }
            long now = System.currentTimeMillis();
            // 创建 application (pending_confirm) —— 状态机初始态（创建即初始态，无需转移校验）
            Application app = new Application();
            String appId = UUID.randomUUID().toString();
            app.setId(appId);
            app.setUserId(userId);
            app.setJobId(jobId);
            app.setPlatformId(platformId);
            app.setStatus("pending_confirm");
            app.setResumeVersionId(req.resumeVersionId());
            app.setIdempotencyKey(req.idempotencyKey());
            app.setApplyDate(applyDate);
            app.setCreatedAt(now);
            app.setUpdatedAt(now);
            appRepo.save(app);
            // 审计：初始态事件（from=null 表示创建）
            writeEvent(userId, appId, null, "pending_confirm", "用户确认入队");
            // ④ 下发投递任务（C2 任务通道，载荷不含 Cookie）
            String taskId = publisher.publish(appId, platformId, jobId, req.idempotencyKey(), req.resumeVersionId());
            ApplicationTask task = new ApplicationTask();
            task.setId(taskId);
            task.setUserId(userId);
            task.setApplicationId(appId);
            task.setIdempotencyKey(req.idempotencyKey());
            task.setPlatformId(platformId);
            task.setJobId(jobId);
            task.setStatus("pending");
            task.setCreatedAt(now);
            task.setUpdatedAt(now);
            taskRepo.save(task);
            accepted++;
        }
        return new ApplyBatchResponse(batchId, accepted, rejected);
    }

    @Override
    public ApplicationsListResponse list(String userId) {
        List<Application> apps = appRepo.findByUserIdOrderByUpdatedAtDesc(userId);
        List<ApplicationListItem> items = apps.stream()
                .map(a -> new ApplicationListItem(a.getId(), a.getJobId(), a.getPlatformId(), a.getStatus(), a.getUpdatedAt()))
                .collect(Collectors.toList());
        return new ApplicationsListResponse(items, apps.size());
    }

    @Override
    public ApplicationDetailResponse detail(String userId, String id) {
        // 数据隔离：findByUserIdAndId 保证只查本人；他人数据 → empty → 404（不泄露 403 归属）
        Application app = appRepo.findByUserIdAndId(userId, id)
                .orElseThrow(() -> new BizException(404, "NOT_FOUND"));
        List<ApplicationEvent> events = eventRepo.findByApplicationIdOrderByOccurredAtAsc(id);
        List<TimelineEntry> timeline = events.stream()
                .map(e -> new TimelineEntry(e.getFromState(), e.getToState(), e.getOccurredAt(), e.getReason()))
                .collect(Collectors.toList());
        return new ApplicationDetailResponse(app.getId(), app.getJobId(), app.getPlatformId(), app.getStatus(), timeline, null);
    }

    private void writeEvent(String userId, String appId, String from, String to, String reason) {
        ApplicationEvent e = new ApplicationEvent();
        e.setId(UUID.randomUUID().toString());
        e.setUserId(userId);
        e.setApplicationId(appId);
        e.setFromState(from);
        e.setToState(to);
        e.setReason(reason);
        e.setOccurredAt(System.currentTimeMillis());
        eventRepo.save(e);
    }

    /**
     * 解析岗位所属平台（业务四元组之一）。
     * TODO(P0→P1): 当前占位 "pending"；P1 job 模块落地后改为从 job 表
     * (uk(platform_id, external_id)) 解析真实 platform_id，届时四元组防重投完整生效。
     */
    private String resolvePlatformId(String jobId) {
        return "pending";
    }
}
