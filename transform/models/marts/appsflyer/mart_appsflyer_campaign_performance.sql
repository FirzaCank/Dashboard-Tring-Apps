-- Mart: campaign performance. Grain: date x media_source x campaign x platform x country.
-- Calculated fields: CTR, CPC, CPI, CPM. All divisions zero-guarded.

select
    date,
    media_source,
    campaign,
    country_code,
    _platform                                                           as platform,
    sum(impressions)                                                    as impressions,
    sum(clicks)                                                         as clicks,
    sum(installs)                                                       as installs,
    sum(cost)                                                           as cost,

    -- CTR = clicks / impressions
    safe_divide(sum(clicks), nullif(sum(impressions), 0))              as ctr,

    -- CPC = cost / clicks
    safe_divide(sum(cost), nullif(sum(clicks), 0))                     as cpc,

    -- CPI = cost / installs
    safe_divide(sum(cost), nullif(sum(installs), 0))                   as cpi,

    -- CPM = cost / impressions * 1000
    safe_divide(sum(cost), nullif(sum(impressions), 0)) * 1000         as cpm

from {{ ref('stg_appsflyer_campaign_performance') }}
group by 1, 2, 3, 4, 5
