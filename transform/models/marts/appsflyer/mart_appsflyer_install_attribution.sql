-- Mart: install attribution. Grain: one row per appsflyer_id per install.

select
    appsflyer_id,
    install_date,
    install_time,
    media_source,
    media_type,
    campaign,
    campaign_id,
    adset,
    ad,
    country_code,
    platform,
    _platform,
    _app_id,
    _ingested_at
from {{ ref('stg_appsflyer_installs') }}
