with source as (
    select * from {{ source('raw', 'raw_listings') }}
)

select
    id,
    title,
    company,
    category,
    date_posted::date            as date_posted,
    url,
    location_restriction,
    salary_raw,
    description_raw,
    scraped_at::timestamp        as scraped_at
from source
where id is not null
  and title is not null
