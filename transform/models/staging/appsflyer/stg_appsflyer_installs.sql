-- Staging: installs. Cast types, derive install_date, dedup to one row per appsflyer_id per install.
-- Dedup strategy: keep the row with the latest _ingested_at for each appsflyer_id.
-- Raw is append-only; re-runs produce duplicates that staging removes here.

with source as (
    select * from {{ source('appsflyer_raw', 'raw_installs') }}
),

typed as (
    select
        `Appsflyer ID`                                  as appsflyer_id,
        safe_cast(`Install Time` as timestamp)          as install_time,
        date(safe_cast(`Install Time` as timestamp))    as install_date,
        `Media Source`                                  as media_source,
        case
            when lower(`Media Source`) = 'organic' then 'organic'
            else 'paid'
        end                                             as media_type,
        `Campaign`                                      as campaign,
        `Campaign ID`                                   as campaign_id,
        `Adset`                                         as adset,
        `Ad`                                            as ad,
        `Country Code`                                  as country_code,
        `Platform`                                      as platform,
        _platform                                       as _platform,
        _app_id,
        _ingested_at,
        _run_id,
        _extract_from,
        _extract_to,
        _schema_flag
    from source
),

deduped as (
    select *
    from typed
    qualify row_number() over (
        partition by appsflyer_id, install_date, _platform
        order by _ingested_at desc
    ) = 1
)

select * from deduped
