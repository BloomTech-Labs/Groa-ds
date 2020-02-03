select review_title, review_text, user_rating
from reviews
where movie_id = '0070948'
	and user_rating Between (
	select avg(user_rating) + stddev(user_rating)
	from reviews
	where movie_id = '0070948'
	and user_rating between 1 and 10
	)
	and 10
limit 10