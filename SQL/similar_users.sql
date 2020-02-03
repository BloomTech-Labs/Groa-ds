select m.primary_title, m.start_year, r.user_rating, ra.average_rating, r.username, r.review_text
from reviews r
join movies m on r.movie_id = m.movie_id
join ratings ra on r.movie_id = ra.movie_id
where username in ('fizz_28','mkrupnick','kwl3000','mau_ner','treywillwest','z1badkarma', 'alexjharrington92','Alan_L_','The_Barnesyard','Andy D')
	AND user_rating BETWEEN 7 AND 10
order by user_rating DESC

