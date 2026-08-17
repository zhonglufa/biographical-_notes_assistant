package com.resumeai.module.jobs.dto;

/** A08 请求（对齐 jobs-favorite.request.schema.json）：action ∈ {favorite, ignore}。 */
public record FavoriteRequest(String action) {
}
