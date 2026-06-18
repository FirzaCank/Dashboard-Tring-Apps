-- Mart: retention. No native API. Built by joining installs + SplashScreen_Loading events.
-- A user installed on cohort_date is retained on D1 if there is activity on cohort_date+1,
-- D7 on cohort_date+7, D30 on cohort_date+30.

with cohort as (
    select
        appsflyer_id,
        install_date            as cohort_date,
        media_source,
        campaign,
        country_code,
        _platform               as platform
    from {{ ref('stg_appsflyer_installs') }}
),

activity as (
    select distinct
        appsflyer_id,
        event_date
    from {{ ref('stg_appsflyer_in_app_events') }}
    where event_name = 'SplashScreen_Loading'
),

cohort_with_retention as (
    select
        c.cohort_date,
        c.media_source,
        c.campaign,
        c.country_code,
        c.platform,
        c.appsflyer_id,
        max(case when a.event_date = date_add(c.cohort_date, interval 1 day)  then 1 else 0 end) as retained_d1,
        max(case when a.event_date = date_add(c.cohort_date, interval 7 day)  then 1 else 0 end) as retained_d7,
        max(case when a.event_date = date_add(c.cohort_date, interval 30 day) then 1 else 0 end) as retained_d30
    from cohort c
    left join activity a on c.appsflyer_id = a.appsflyer_id
    group by 1, 2, 3, 4, 5, 6
),

aggregated as (
    select
        cohort_date,
        media_source,
        campaign,
        country_code,
        platform,
        count(*)                    as cohort_size,
        sum(retained_d1)            as retained_d1,
        sum(retained_d7)            as retained_d7,
        sum(retained_d30)           as retained_d30
    from cohort_with_retention
    group by 1, 2, 3, 4, 5
)

select
    cohort_date,
    media_source,
    campaign,
    country_code,
    platform,
    cohort_size,
    retained_d1,
    retained_d7,
    retained_d30,

    -- d1_retention = retained_d1 / cohort_size
    safe_divide(retained_d1, nullif(cohort_size, 0))    as d1_retention,

    -- d7_retention = retained_d7 / cohort_size
    safe_divide(retained_d7, nullif(cohort_size, 0))    as d7_retention,

    -- d30_retention = retained_d30 / cohort_size
    safe_divide(retained_d30, nullif(cohort_size, 0))   as d30_retention

from aggregated
