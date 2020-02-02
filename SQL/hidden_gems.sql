SELECT  m.primary_title, m.start_year, ra.num_votes num,
                                    ra.average_rating avgr, r.user_rating taste,
                                    r.username, r.review_text txt, m.movie_id mid
                            FROM reviews r
                            JOIN movies m ON r.movie_id = m.movie_id
                            JOIN ratings ra ON r.movie_id = ra.movie_id
                            WHERE username IN ('fizz_28','mkrupnick','kwl3000','mau_ner','z1badkarma', 'alexjharrington92','Alan_L_','The_Barnesyard','Andy D')
                                AND user_rating BETWEEN 7 AND 10
								AND ra.average_rating BETWEEN 7 AND 10
								AND ra.num_votes <= 1000
                            ORDER BY user_rating DESC
                            LIMIT 50