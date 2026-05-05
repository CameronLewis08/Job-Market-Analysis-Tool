with listings as (
    select id as listing_id, date_posted, salary_raw
    from {{ ref('stg_listings') }}
),

salary_tokens as (
    select
        l.listing_id,
        l.date_posted,
        case
            when token_value ilike '%k'
                then regexp_replace(lower(token_value), '[^0-9.]', '', 'g')::numeric * 1000
            else regexp_replace(token_value, '[^0-9.]', '', 'g')::numeric
        end as salary_value
    from listings l
    cross join lateral regexp_matches(
        coalesce(l.salary_raw, ''),
        '([0-9][0-9,]*(?:\.[0-9]+)?\s*[kK]?)',
        'g'
    ) with ordinality as token(match_text, token_index)
    cross join lateral (
        select token.match_text[1] as token_value
    ) extracted
),

listing_salary as (
    select
        listing_id,
        date_posted,
        min(salary_value) as salary_min,
        avg(salary_value) as salary_avg,
        max(salary_value) as salary_max
    from salary_tokens
    group by listing_id, date_posted
),

coverage as (
    select
        count(*) as total_listings,
        (
            select count(distinct listing_id)
            from listing_salary
        ) as listings_with_salary
    from listings
),

skill_mentions as (
    select distinct listing_id, skill, skill_category
    from {{ ref('int_listing_skills') }}
)

select
    sm.skill,
    sm.skill_category,
    min(ls.salary_min)                    as min_salary,
    avg(ls.salary_avg)::numeric(12, 2)    as avg_salary,
    max(ls.salary_max)                    as max_salary,
    min(ls.date_posted)                   as first_seen,
    max(ls.date_posted)                   as last_seen,
    (
        100.0 * c.listings_with_salary / nullif(c.total_listings, 0)
    )::numeric(5, 2)                      as coverage_pct
from skill_mentions sm
join listing_salary ls
    on sm.listing_id = ls.listing_id
cross join coverage c
group by sm.skill, sm.skill_category, c.listings_with_salary, c.total_listings
order by avg_salary desc
