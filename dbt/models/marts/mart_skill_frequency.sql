with skill_mentions as (
    select * from {{ ref('int_listing_skills') }}
)

select
    skill,
    skill_category,
    count(distinct listing_id) as listing_count,
    min(date_posted)           as first_seen,
    max(date_posted)           as last_seen
from skill_mentions
group by skill, skill_category
order by listing_count desc
