package com.resumeai.module.jobs.dto;

/** A08 响应（对齐 jobs-favorite.response.schema.json）：ok + favoriteId? + status。 */
public record FavoriteResponse(boolean ok, String favoriteId, String status) {
}
