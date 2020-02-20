select 	username, 
		count(user_rating), 
		round(avg(user_rating), 2) avg_rating, 
		round(stddev(user_rating), 2) stdv_rating,
		round(avg(ra.average_rating):: numeric, 2) avg_score,
		round(stddev(ra.average_rating):: numeric, 2) stdv_score,
		round(avg(m.start_year)) avg_year,
		round(stddev(m.start_year):: numeric, 2) stdv_year,
from reviews re
join ratings ra on ra.movie_id = re.movie_id
join movies m on m.movie_id = re.movie_id
where m.start_year between 1900 and 2020
	and re.user_rating < 11
group by username
having count(re.user_rating) > 20
--order by stdv_rating DESC