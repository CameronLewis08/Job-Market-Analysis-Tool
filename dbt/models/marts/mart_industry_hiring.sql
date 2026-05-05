with listings as (
    select id as listing_id, category, date_posted
    from {{ ref('stg_listings') }}
    where category is not null
      and date_posted is not null
)

select
    date_trunc('week', date_posted)::date as week_start,
    category,
    count(distinct listing_id)            as listing_count
from listings
group by 1, 2
order by week_start, listing_count desc
