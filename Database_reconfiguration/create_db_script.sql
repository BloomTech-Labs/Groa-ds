-- SEQUENCE: public.movie_lists_id_seq

CREATE SEQUENCE public.movie_lists_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

-- SEQUENCE: public.movie_provider_id_seq

CREATE SEQUENCE public.movie_provider_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.provider_id_seq

CREATE SEQUENCE public.provider_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;

-- SEQUENCE: public.rec_id_seq

CREATE SEQUENCE public.rec_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.willnotwatch_id_seq

CREATE SEQUENCE public.willnotwatch_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.movie_review_id_seq

CREATE SEQUENCE public.movie_review_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.user_rating_id_seq

CREATE SEQUENCE public.user_rating_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.user_review_id_seq

CREATE SEQUENCE public.user_review_id_seq
    INCREMENT 1
    START 1
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- SEQUENCE: public.user_watchlist_id_seq

CREATE SEQUENCE public.user_watchlist_id_seq
    INCREMENT 1
    START 120832
    MINVALUE 1
    MAXVALUE 9223372036854775807
    CACHE 1;


-- Table: public.movies

CREATE TABLE public.movies
(
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    title_type character varying COLLATE pg_catalog."default",
    primary_title character varying COLLATE pg_catalog."default",
    original_title character varying COLLATE pg_catalog."default",
    is_adult boolean,
    start_year integer,
    end_year integer,
    runtime_minutes integer,
    genres character varying COLLATE pg_catalog."default",
    poster_url character varying COLLATE pg_catalog."default",
    average_rating real,
    num_votes integer,
    original_language character varying COLLATE pg_catalog."default",
    description character varying COLLATE pg_catalog."default",
    trailer_url character varying COLLATE pg_catalog."default",
    CONSTRAINT movies_pkey PRIMARY KEY (movie_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.movie_reviews

CREATE TABLE public.movie_reviews
(
    review_id bigint NOT NULL DEFAULT nextval('movie_review_id_seq'::regclass),
    movie_id character varying COLLATE pg_catalog."default",
    review_date date,
    user_rating real,
    helpful_num integer,
    helpful_denom integer,
    user_name character varying COLLATE pg_catalog."default",
    review_text character varying COLLATE pg_catalog."default",
    review_title character varying COLLATE pg_catalog."default",
    source text COLLATE pg_catalog."default",
    CONSTRAINT movie_reviews_pk PRIMARY KEY (review_id),
    CONSTRAINT mr_movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.users

CREATE TABLE public.users
(
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
	email character varying COLLATE pg_catalog."default",
    has_letterboxd boolean,
    has_imdb boolean,
    CONSTRAINT users_pkey PRIMARY KEY (user_id),
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.user_willnotwatchlist

CREATE TABLE public.user_willnotwatchlist
(
    id integer NOT NULL DEFAULT nextval('willnotwatch_id_seq'::regclass),
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    CONSTRAINT user_willnotwatchlist_pk PRIMARY KEY (id),
    CONSTRAINT uwnw_movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT uwnw_user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.user_watchlist

CREATE TABLE public.user_watchlist
(
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    source character varying COLLATE pg_catalog."default",
    id integer NOT NULL DEFAULT nextval('user_watchlist_id_seq'::regclass),
    CONSTRAINT user_watchlist_pkey PRIMARY KEY (id),
    CONSTRAINT movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.user_watched

CREATE TABLE public.user_watched
(
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    date date NOT NULL,
    source character varying COLLATE pg_catalog."default",
    CONSTRAINT user_watched_pk PRIMARY KEY (user_id, movie_id, date),
    CONSTRAINT watched_movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT watched_user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.user_reviews

CREATE TABLE public.user_reviews
(
    review_id integer NOT NULL DEFAULT nextval('user_review_id_seq'::regclass),
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    date date,
    review_title character varying COLLATE pg_catalog."default",
    review_text character varying COLLATE pg_catalog."default",
    tags character varying COLLATE pg_catalog."default",
    source character varying COLLATE pg_catalog."default",
    CONSTRAINT user_reviews_pk PRIMARY KEY (review_id),
    CONSTRAINT urev_movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT urev_user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.user_ratings

CREATE TABLE public.user_ratings
(
    rating_id integer NOT NULL DEFAULT nextval('user_rating_id_seq'::regclass),
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    movie_id character varying COLLATE pg_catalog."default",
    date date,
    rating real,
    source character varying COLLATE pg_catalog."default",
    CONSTRAINT user_ratings_pk PRIMARY KEY (rating_id),
    CONSTRAINT ur_movie_id_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT ur_user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.recommendations

CREATE TABLE public.recommendations
(
    recommendation_id integer NOT NULL DEFAULT nextval('rec_id_seq'::regclass),
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    date timestamp with time zone,
    model_type character varying COLLATE pg_catalog."default",
    num_recs integer,
    good_threshold integer,
    bad_threshold integer,
    harshness integer,
    CONSTRAINT recommendations_pkey PRIMARY KEY (recommendation_id),
    CONSTRAINT rec_user_id_fk FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.recommendations_movies

CREATE TABLE public.recommendations_movies
(
    recommendation_id integer NOT NULL,
    movie_number integer NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    interaction boolean,
    CONSTRAINT recommendations_movies_pkey PRIMARY KEY (recommendation_id, movie_number),
    CONSTRAINT movie_recommendation_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT recommendation_fk FOREIGN KEY (recommendation_id)
        REFERENCES public.recommendations (recommendation_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
    
-- Table: public.providers

CREATE TABLE public.providers
(
    provider_id integer NOT NULL DEFAULT nextval('provider_id_seq'::regclass),
    name character varying COLLATE pg_catalog."default" NOT NULL,
    logo_url character varying COLLATE pg_catalog."default",
    CONSTRAINT providers_pkey PRIMARY KEY (provider_id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

    
-- Table: public.movie_providers

CREATE TABLE public.movie_providers
(
    id integer NOT NULL DEFAULT nextval('movie_provider_id_seq'::regclass),    
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    provider_id integer NOT NULL,
    provider_movie_url character varying COLLATE pg_catalog."default",
    presentation_type character varying COLLATE pg_catalog."default",
    monetization_type character varying COLLATE pg_catalog."default",
    CONSTRAINT movie_providers_pkey PRIMARY KEY (id),
    CONSTRAINT provider_movie_fk FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT providers_fk FOREIGN KEY (provider_id)
        REFERENCES public.providers (provider_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.movie_lists

CREATE TABLE public.movie_lists
(
    list_id integer NOT NULL DEFAULT nextval('movie_lists_id_seq'::regclass),
    user_id character varying COLLATE pg_catalog."default" NOT NULL,
    name character varying COLLATE pg_catalog."default",
    private boolean,
    CONSTRAINT movie_lists_pkey PRIMARY KEY (list_id),
    CONSTRAINT movie_lists_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public.users (user_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


-- Table: public.list_movies

CREATE TABLE public.list_movies
(
    list_id integer NOT NULL,
    movie_id character varying COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT list_movies_pkey PRIMARY KEY (list_id, movie_id),
    CONSTRAINT list_movies_list_id_fkey FOREIGN KEY (list_id)
        REFERENCES public.movie_lists (list_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT list_movies_movie_id_fkey FOREIGN KEY (movie_id)
        REFERENCES public.movies (movie_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
