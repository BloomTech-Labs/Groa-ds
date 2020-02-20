select  m.movie_id, 
		primary_title title, 
		ra.average_rating, 
		ra.num_votes, 
		start_year, 
		runtime_minutes, 
		genres
from movies m
join ratings ra on ra.movie_id = m.movie_id
where m.title_type = 'movie'
	and ra.num_votes > 1000
	and m.start_year < 2020
	and m.genres ilike '%horror%'
order by ra.average_rating DESC
limit 200