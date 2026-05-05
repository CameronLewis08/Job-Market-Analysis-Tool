with listings as (
    select * from {{ ref('stg_listings') }}
    where description_raw is not null
),

skills as (
    select * from {{ ref('skills') }}
)

select
    l.id         as listing_id,
    l.date_posted,
    l.category   as listing_category,
    s.skill,
    s.category   as skill_category
from listings l
cross join skills s
where l.description_raw ~* ('\m' || regexp_replace(s.skill, '([.+*?^${}()|[\]\\])', '\\\1', 'g') || '\m')
