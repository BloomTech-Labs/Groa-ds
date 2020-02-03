with matches as (
						select m.movie_id mid, m.primary_title tit, m.start_year, r.user_rating taste, ra.average_rating avgr, r.username, r.review_text txt
						from reviews r
						join movies m on r.movie_id = m.movie_id
						join ratings ra on r.movie_id = ra.movie_id
						where username in ('fizz_28','mkrupnick','kwl3000','mau_ner','z1badkarma', 'alexjharrington92','Alan_L_','The_Barnesyard','Andy D')
							AND user_rating BETWEEN 7 AND 10
						order by user_rating DESC
						),

deviations as (
					select distinct(rr.movie_id) mid, stddev(rev.user_rating) std, rr.average_rating as avgr
					from ratings rr
					join reviews rev on rev.movie_id = rr.movie_id
					group by rr.movie_id)
select deviations.mid, matches.tit, matches.taste, deviations.avgr, deviations.std, matches.txt
from deviations
join matches on matches.mid = deviations.mid
where matches.taste > ((1.5*deviations.std)+deviations.avgr)
	and matches.taste < 11
order by (matches.taste-deviations.avgr)/deviations.std
limit 50


