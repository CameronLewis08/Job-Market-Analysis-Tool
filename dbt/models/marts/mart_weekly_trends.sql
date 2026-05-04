with skill_mentions as (
    select * from {{ ref('int_listing_skills') }}
)

select
    date_trunc('week', date_posted)::date as week_start,
    skill,
    skill_category,
    count(distinct listing_id)            as listing_count
from skill_mentions
group by 1, 2, 3
order by week_start, listing_count desc
