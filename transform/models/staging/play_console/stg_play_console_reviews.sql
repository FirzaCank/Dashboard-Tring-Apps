-- Staging: user reviews. Cast types, dedup to one row per review_id (latest ingest).
-- Reviews are not date-scoped: the API always returns the current state of all reviews.
-- developer_reply fields are null when no reply has been posted.

with source as (
    select * from {{ source('play_raw', 'raw_reviews') }}
),

typed as (
    select
        review_id,
        author_name,
        text                                                        as review_text,
        safe_cast(star_rating as int64)                             as star_rating,
        reviewer_language,
        device,
        safe_cast(android_os_version as int64)                      as android_os_version,
        safe_cast(app_version_code as int64)                        as app_version_code,
        app_version_name,

        -- device metadata
        device_product_name,
        device_manufacturer,
        device_class,
        safe_cast(device_ram_mb as int64)                           as device_ram_mb,

        -- timestamps stored as unix epoch seconds
        safe_cast(last_modified_seconds as int64)                   as last_modified_at,
        timestamp_seconds(
            safe_cast(last_modified_seconds as int64)
        )                                                           as last_modified_at_ts,

        -- developer reply (null when no reply posted)
        nullif(developer_reply_text, '')                            as developer_reply_text,
        safe_cast(
            nullif(developer_reply_seconds, '') as int64
        )                                                           as developer_reply_at,
        case
            when nullif(developer_reply_seconds, '') is null then null
            else timestamp_seconds(safe_cast(developer_reply_seconds as int64))
        end                                                         as developer_reply_at_ts,

        _ingested_at,
        _source,
        _run_id
    from source
),

deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by review_id
        order by _ingested_at desc
    ) = 1
)

select * from deduped
