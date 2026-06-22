-- Mart: user reviews with reply status and rating distribution.
-- Grain: one row per review_id (deduped in staging).
-- Partitioned by review date (derived from last_modified_at epoch), clustered by star_rating.

select
    review_id,
    author_name,
    review_text,
    star_rating,
    reviewer_language,
    device,
    android_os_version,
    app_version_code,
    app_version_name,

    device_product_name,
    device_manufacturer,
    device_class,
    device_ram_mb,

    last_modified_at,
    last_modified_at_ts,
    date(last_modified_at_ts)                               as review_date,

    developer_reply_text,
    developer_reply_at,
    developer_reply_at_ts,

    -- convenience flags for dashboard filtering
    developer_reply_text is not null                        as has_developer_reply,
    star_rating <= 2                                        as is_negative_review,

    _ingested_at,
    _source,
    _run_id

from {{ ref('stg_play_console_reviews') }}
