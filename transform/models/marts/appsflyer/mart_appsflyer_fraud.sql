-- Mart: fraud detection. Grain: date x media_source x campaign x platform x country.
-- fraud_rate = blocked_installs / (installs + blocked_installs). Zero-guarded.

with blocked as (
    select
        install_date                    as date,
        media_source,
        campaign,
        country_code,
        _platform                       as platform,
        count(*)                        as blocked_installs,
        count(*)                        as fraud_installs
    from {{ ref('stg_appsflyer_blocked_installs') }}
    group by 1, 2, 3, 4, 5
),

installs as (
    select
        install_date                    as date,
        media_source,
        campaign,
        country_code,
        _platform                       as platform,
        count(*)                        as installs
    from {{ ref('stg_appsflyer_installs') }}
    group by 1, 2, 3, 4, 5
)

select
    coalesce(b.date, i.date)                        as date,
    coalesce(b.media_source, i.media_source)        as media_source,
    coalesce(b.campaign, i.campaign)                as campaign,
    coalesce(b.country_code, i.country_code)        as country_code,
    coalesce(b.platform, i.platform)                as platform,
    coalesce(b.blocked_installs, 0)                 as blocked_installs,
    coalesce(b.fraud_installs, 0)                   as fraud_installs,
    coalesce(i.installs, 0)                         as installs,

    -- fraud_rate = blocked / (installs + blocked)
    safe_divide(
        coalesce(b.blocked_installs, 0),
        nullif(coalesce(i.installs, 0) + coalesce(b.blocked_installs, 0), 0)
    )                                               as fraud_rate

from blocked b
full outer join installs i
    on b.date = i.date
    and b.media_source = i.media_source
    and b.campaign = i.campaign
    and b.country_code = i.country_code
    and b.platform = i.platform
