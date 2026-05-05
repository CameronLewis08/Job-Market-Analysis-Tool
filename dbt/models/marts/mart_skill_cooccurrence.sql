with skill_mentions as (
    select distinct listing_id, skill
    from {{ ref('int_listing_skills') }}
),

skill_pairs as (
    select
        left_skill.skill  as skill_a,
        right_skill.skill as skill_b,
        left_skill.listing_id
    from skill_mentions left_skill
    join skill_mentions right_skill
        on left_skill.listing_id = right_skill.listing_id
       and left_skill.skill < right_skill.skill
)

select
    skill_a,
    skill_b,
    count(distinct listing_id) as cooccurrence_count
from skill_pairs
group by 1, 2
having count(distinct listing_id) >= 2
order by cooccurrence_count desc, skill_a, skill_b
