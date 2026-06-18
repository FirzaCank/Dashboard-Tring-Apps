-- Staging: in-app events. Cast types, map event_name to category via seed.

with source as (
    select * from {{ source('appsflyer_raw', 'raw_in_app_events') }}
),

mapping as (
    select * from {{ ref('appsflyer_event_mapping') }}
),

typed as (
    select
        `Appsflyer ID`                              as appsflyer_id,
        `Event Name`                                as event_name,
        safe_cast(`Event Time` as timestamp)        as event_time,
        date(safe_cast(`Event Time` as timestamp))  as event_date,
        `Media Source`                              as media_source,
        `Campaign`                                  as campaign,
        `Campaign ID`                               as campaign_id,
        `Country Code`                              as country_code,
        `Platform`                                  as platform,
        _platform,
        _app_id,
        _ingested_at,
        _run_id,
        _extract_from,
        _extract_to,
        _schema_flag
    from source
)

select
    t.*,
    m.category as event_category
from typed t
left join mapping m on t.event_name = m.event_name
