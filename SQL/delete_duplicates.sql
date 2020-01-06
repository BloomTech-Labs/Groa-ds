-- deletes duplicate reviews

delete
from reviews a 
	using reviews b
where
	a.username = b.username
	and a.review_title = b.review_title
