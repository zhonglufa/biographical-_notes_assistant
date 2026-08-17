package com.resumeai.module.jobs.entity;

import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.io.Serializable;

/** 复合主键（user_id, job_id）· 对齐 LLD-数据库设计 job_match。作为 @IdClass 使用。 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class JobMatchId implements Serializable {
    private String userId;
    private Long jobId;
}
