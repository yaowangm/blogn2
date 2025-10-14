--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: cleanup_orphaned_vectors(); Type: FUNCTION; Schema: public; Owner: wy
--

CREATE FUNCTION public.cleanup_orphaned_vectors() RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- 清理孤立的文章向量
    DELETE FROM article_vectors 
    WHERE projectitem_id NOT IN (SELECT id FROM projectitem);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- 清理孤立的片段向量
    DELETE FROM content_segment_vectors 
    WHERE article_vector_id NOT IN (SELECT id FROM article_vectors);
    
    -- 清理孤立的评论向量
    DELETE FROM comment_vectors 
    WHERE post_id NOT IN (SELECT id FROM post);
    
    RETURN deleted_count;
END;
$$;


ALTER FUNCTION public.cleanup_orphaned_vectors() OWNER TO wy;

--
-- Name: get_vectorization_stats(); Type: FUNCTION; Schema: public; Owner: wy
--

CREATE FUNCTION public.get_vectorization_stats() RETURNS TABLE(total_articles integer, vectorized_articles integer, total_segments bigint, avg_segments_per_article numeric, total_comments integer, vectorized_comments integer)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*)::INTEGER FROM projectitem WHERE status = 1) as total_articles,
        (SELECT COUNT(*)::INTEGER FROM article_vectors) as vectorized_articles,
        (SELECT COUNT(*) FROM content_segment_vectors) as total_segments,
        (SELECT COALESCE(AVG(segment_count), 0) FROM article_vectors) as avg_segments_per_article,
        (SELECT COUNT(*)::INTEGER FROM post WHERE projectitemid > 0) as total_comments,
        (SELECT COUNT(*)::INTEGER FROM comment_vectors) as vectorized_comments;
END;
$$;


ALTER FUNCTION public.get_vectorization_stats() OWNER TO wy;

--
-- Name: promote_fdw_tables(text, text); Type: FUNCTION; Schema: public; Owner: wy
--

CREATE FUNCTION public.promote_fdw_tables(from_schema text, to_schema text) RETURNS void
    LANGUAGE plpgsql
    AS $$
DECLARE
  tbl RECORD;
BEGIN
  FOR tbl IN
    SELECT relname AS table_name
    FROM pg_foreign_table ft
    JOIN pg_class c ON c.oid = ft.ftrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = from_schema
  LOOP
    RAISE NOTICE 'Processing table: %', tbl.table_name;
    -- 复制到目标 schema
    EXECUTE format('CREATE TABLE %I.%I AS TABLE %I.%I', to_schema, tbl.table_name, from_schema, tbl.table_name);
    -- 删除外部表
    EXECUTE format('DROP FOREIGN TABLE %I.%I', from_schema, tbl.table_name);
  END LOOP;
END;
$$;


ALTER FUNCTION public.promote_fdw_tables(from_schema text, to_schema text) OWNER TO wy;

--
-- Name: update_article_vectors_updated_at(); Type: FUNCTION; Schema: public; Owner: wy
--

CREATE FUNCTION public.update_article_vectors_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_article_vectors_updated_at() OWNER TO wy;

--
-- Name: update_comment_vectors_updated_at(); Type: FUNCTION; Schema: public; Owner: wy
--

CREATE FUNCTION public.update_comment_vectors_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_comment_vectors_updated_at() OWNER TO wy;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: article_vectors; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.article_vectors (
    id integer NOT NULL,
    projectitem_id integer,
    title_vector public.vector(384),
    title_text text,
    content_vector public.vector(384),
    content_text text,
    segment_count integer DEFAULT 1,
    vectorization_method character varying(50) DEFAULT 'direct'::character varying,
    total_text_length integer,
    max_segment_length integer,
    aggregation_weights jsonb,
    overlap_strategy character varying(20) DEFAULT 'sliding_window'::character varying,
    window_size integer DEFAULT 400,
    step_size integer DEFAULT 200,
    avg_confidence double precision DEFAULT 1.0,
    key_segment_ratio double precision DEFAULT 0.0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_avg_confidence CHECK (((avg_confidence >= (0.0)::double precision) AND (avg_confidence <= (1.0)::double precision))),
    CONSTRAINT chk_key_segment_ratio CHECK (((key_segment_ratio >= (0.0)::double precision) AND (key_segment_ratio <= (1.0)::double precision))),
    CONSTRAINT chk_segment_count CHECK ((segment_count > 0))
);


ALTER TABLE public.article_vectors OWNER TO wy;

--
-- Name: TABLE article_vectors; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON TABLE public.article_vectors IS '文章向量表 - 使用 paraphrase-multilingual-MiniLM-L12-v2 模型 (384维)';


--
-- Name: COLUMN article_vectors.title_vector; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.article_vectors.title_vector IS '标题向量 (384维) - paraphrase-multilingual-MiniLM-L12-v2';


--
-- Name: COLUMN article_vectors.content_vector; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.article_vectors.content_vector IS '内容向量 (384维) - paraphrase-multilingual-MiniLM-L12-v2';


--
-- Name: project; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.project (
    id bigint NOT NULL,
    name character varying(100),
    comment text,
    recordcount integer,
    accesscount integer,
    userid integer,
    folderid integer,
    createtime timestamp without time zone,
    state integer,
    lastitem integer,
    updatetime timestamp without time zone,
    commentcount integer
);


ALTER TABLE public.project OWNER TO wy;

--
-- Name: projectitem; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.projectitem (
    id bigint NOT NULL,
    projectid integer,
    name character varying(100),
    comment text,
    itemtype integer,
    itemsize integer,
    attachment character varying(200),
    linkstr character varying(200),
    userid integer,
    accesscount integer,
    updatetime timestamp without time zone,
    commentcount integer,
    createtime timestamp without time zone,
    folderid integer,
    lastmodifytime timestamp without time zone,
    status integer,
    allowpost integer
);


ALTER TABLE public.projectitem OWNER TO wy;

--
-- Name: users; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.users (
    id bigint NOT NULL,
    name character(50),
    password character varying(60),
    state integer,
    email character(50),
    regtime timestamp without time zone,
    iplog character(15),
    projectid integer,
    point integer,
    lastupdate timestamp without time zone,
    intropiid bigint
);


ALTER TABLE public.users OWNER TO wy;

--
-- Name: article_vector_details; Type: VIEW; Schema: public; Owner: wy
--

CREATE VIEW public.article_vector_details AS
 SELECT av.id,
    av.projectitem_id,
    av.title_text,
    av.content_text,
    av.segment_count,
    av.vectorization_method,
    av.total_text_length,
    av.avg_confidence,
    av.key_segment_ratio,
    av.created_at,
    av.updated_at,
    pi.name AS article_name,
    pi.comment AS article_content,
    p.name AS project_name,
    u.name AS author_name
   FROM (((public.article_vectors av
     LEFT JOIN public.projectitem pi ON ((av.projectitem_id = pi.id)))
     LEFT JOIN public.project p ON ((pi.projectid = p.id)))
     LEFT JOIN public.users u ON ((pi.userid = u.id)));


ALTER VIEW public.article_vector_details OWNER TO wy;

--
-- Name: article_vectors_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.article_vectors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.article_vectors_id_seq OWNER TO wy;

--
-- Name: article_vectors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.article_vectors_id_seq OWNED BY public.article_vectors.id;


--
-- Name: attachment; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.attachment (
    id bigint NOT NULL,
    parentid bigint,
    amtype integer,
    comment character varying(200),
    linkstr character varying(200),
    createtime timestamp without time zone,
    updatetime timestamp without time zone
);


ALTER TABLE public.attachment OWNER TO wy;

--
-- Name: attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attachment_id_seq OWNER TO wy;

--
-- Name: attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.attachment_id_seq OWNED BY public.attachment.id;


--
-- Name: comment_vectors; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.comment_vectors (
    id integer NOT NULL,
    post_id integer,
    title_vector public.vector(384),
    content_vector public.vector(384),
    title_text text,
    content_text text,
    segment_count integer DEFAULT 1,
    vectorization_method character varying(50) DEFAULT 'direct'::character varying,
    total_text_length integer,
    max_segment_length integer,
    avg_confidence double precision DEFAULT 1.0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_comment_avg_confidence CHECK (((avg_confidence >= (0.0)::double precision) AND (avg_confidence <= (1.0)::double precision))),
    CONSTRAINT chk_comment_segment_count CHECK ((segment_count > 0))
);


ALTER TABLE public.comment_vectors OWNER TO wy;

--
-- Name: TABLE comment_vectors; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON TABLE public.comment_vectors IS '评论向量表 - 使用 paraphrase-multilingual-MiniLM-L12-v2 模型 (384维)';


--
-- Name: COLUMN comment_vectors.title_vector; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.comment_vectors.title_vector IS '评论标题向量 (384维) - paraphrase-multilingual-MiniLM-L12-v2';


--
-- Name: COLUMN comment_vectors.content_vector; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.comment_vectors.content_vector IS '评论内容向量 (384维) - paraphrase-multilingual-MiniLM-L12-v2';


--
-- Name: comment_vectors_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.comment_vectors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.comment_vectors_id_seq OWNER TO wy;

--
-- Name: comment_vectors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.comment_vectors_id_seq OWNED BY public.comment_vectors.id;


--
-- Name: content_segment_vectors; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.content_segment_vectors (
    id integer NOT NULL,
    article_vector_id integer,
    segment_index integer NOT NULL,
    segment_hash character varying(64),
    segment_text text,
    segment_vector public.vector(384),
    segment_length integer,
    token_count integer,
    word_count integer,
    start_char_pos integer,
    end_char_pos integer,
    start_token_pos integer,
    end_token_pos integer,
    prev_overlap_chars integer DEFAULT 0,
    next_overlap_chars integer DEFAULT 0,
    overlap_ratio double precision DEFAULT 0.0,
    confidence_score double precision DEFAULT 1.0,
    semantic_density double precision,
    keyword_density double precision,
    is_key_segment boolean DEFAULT false,
    segment_type character varying(20) DEFAULT 'body'::character varying,
    contains_title boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_confidence_score CHECK (((confidence_score >= (0.0)::double precision) AND (confidence_score <= (1.0)::double precision))),
    CONSTRAINT chk_overlap_ratio CHECK (((overlap_ratio >= (0.0)::double precision) AND (overlap_ratio <= (1.0)::double precision))),
    CONSTRAINT chk_segment_index CHECK ((segment_index >= 0)),
    CONSTRAINT chk_segment_length CHECK ((segment_length > 0))
);


ALTER TABLE public.content_segment_vectors OWNER TO wy;

--
-- Name: TABLE content_segment_vectors; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON TABLE public.content_segment_vectors IS '内容片段向量表 - 使用 paraphrase-multilingual-MiniLM-L12-v2 模型 (384维)';


--
-- Name: COLUMN content_segment_vectors.segment_vector; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.content_segment_vectors.segment_vector IS '片段向量 (384维) - paraphrase-multilingual-MiniLM-L12-v2';


--
-- Name: content_segment_vectors_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.content_segment_vectors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.content_segment_vectors_id_seq OWNER TO wy;

--
-- Name: content_segment_vectors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.content_segment_vectors_id_seq OWNED BY public.content_segment_vectors.id;


--
-- Name: folders; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.folders (
    id bigint NOT NULL,
    name character(100),
    comment character(200),
    parent integer,
    subitemcount integer,
    postcount integer,
    recordcount integer,
    projectid integer,
    ordernum integer
);


ALTER TABLE public.folders OWNER TO wy;

--
-- Name: folders_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.folders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.folders_id_seq OWNER TO wy;

--
-- Name: folders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.folders_id_seq OWNED BY public.folders.id;


--
-- Name: forumlist; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.forumlist (
    id bigint NOT NULL,
    name character(50),
    comment character(200),
    artcount integer
);


ALTER TABLE public.forumlist OWNER TO wy;

--
-- Name: forumlist_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.forumlist_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.forumlist_id_seq OWNER TO wy;

--
-- Name: forumlist_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.forumlist_id_seq OWNED BY public.forumlist.id;


--
-- Name: glovar; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.glovar (
    id bigint NOT NULL,
    varname character(50),
    varvalue integer
);


ALTER TABLE public.glovar OWNER TO wy;

--
-- Name: glovar_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.glovar_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.glovar_id_seq OWNER TO wy;

--
-- Name: glovar_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.glovar_id_seq OWNED BY public.glovar.id;


--
-- Name: iptable; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.iptable (
    id bigint NOT NULL,
    ip character(15),
    createtime timestamp without time zone,
    state integer
);


ALTER TABLE public.iptable OWNER TO wy;

--
-- Name: iptable_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.iptable_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.iptable_id_seq OWNER TO wy;

--
-- Name: iptable_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.iptable_id_seq OWNED BY public.iptable.id;


--
-- Name: levels; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.levels (
    id bigint NOT NULL,
    name character(20)
);


ALTER TABLE public.levels OWNER TO wy;

--
-- Name: levels_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.levels_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.levels_id_seq OWNER TO wy;

--
-- Name: levels_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.levels_id_seq OWNED BY public.levels.id;


--
-- Name: point_logs; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.point_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    points integer NOT NULL,
    source character varying(50) NOT NULL,
    log_date timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.point_logs OWNER TO wy;

--
-- Name: TABLE point_logs; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON TABLE public.point_logs IS '积分记录表，用于跟踪用户每日积分获得情况';


--
-- Name: COLUMN point_logs.user_id; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.user_id IS '用户ID';


--
-- Name: COLUMN point_logs.points; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.points IS '获得的积分数';


--
-- Name: COLUMN point_logs.source; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.source IS '积分来源：article_create, regkey_exchange等';


--
-- Name: COLUMN point_logs.log_date; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.log_date IS '积分记录日期';


--
-- Name: COLUMN point_logs.created_at; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.created_at IS '记录创建时间';


--
-- Name: COLUMN point_logs.updated_at; Type: COMMENT; Schema: public; Owner: wy
--

COMMENT ON COLUMN public.point_logs.updated_at IS '记录更新时间';


--
-- Name: point_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.point_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.point_logs_id_seq OWNER TO wy;

--
-- Name: point_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.point_logs_id_seq OWNED BY public.point_logs.id;


--
-- Name: post; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.post (
    id bigint NOT NULL,
    folderid integer,
    rootid integer,
    userid integer,
    subject character varying(200),
    content text,
    size integer,
    status integer,
    hits integer,
    posttime timestamp without time zone,
    lastreplytime timestamp without time zone,
    lastreplyid integer,
    projectitemid integer,
    replycount integer,
    userip character(15)
);


ALTER TABLE public.post OWNER TO wy;

--
-- Name: post_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.post_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.post_id_seq OWNER TO wy;

--
-- Name: post_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.post_id_seq OWNED BY public.post.id;


--
-- Name: project_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.project_id_seq OWNER TO wy;

--
-- Name: project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.project_id_seq OWNED BY public.project.id;


--
-- Name: projectitem_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.projectitem_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projectitem_id_seq OWNER TO wy;

--
-- Name: projectitem_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.projectitem_id_seq OWNED BY public.projectitem.id;


--
-- Name: regkey; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.regkey (
    id bigint NOT NULL,
    name character(25),
    ownerid bigint,
    userid bigint,
    status integer,
    createtime timestamp without time zone
);


ALTER TABLE public.regkey OWNER TO wy;

--
-- Name: regkey_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.regkey_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.regkey_id_seq OWNER TO wy;

--
-- Name: regkey_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.regkey_id_seq OWNED BY public.regkey.id;


--
-- Name: relation; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.relation (
    id bigint NOT NULL,
    projectid integer,
    objectid integer,
    created timestamp without time zone,
    acttype integer
);


ALTER TABLE public.relation OWNER TO wy;

--
-- Name: relation_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.relation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.relation_id_seq OWNER TO wy;

--
-- Name: relation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.relation_id_seq OWNED BY public.relation.id;


--
-- Name: segment_vector_details; Type: VIEW; Schema: public; Owner: wy
--

CREATE VIEW public.segment_vector_details AS
 SELECT csv.id,
    csv.article_vector_id,
    csv.segment_index,
    csv.segment_text,
    csv.segment_length,
    csv.confidence_score,
    csv.is_key_segment,
    csv.segment_type,
    csv.created_at,
    av.projectitem_id,
    pi.name AS article_name
   FROM ((public.content_segment_vectors csv
     LEFT JOIN public.article_vectors av ON ((csv.article_vector_id = av.id)))
     LEFT JOIN public.projectitem pi ON ((av.projectitem_id = pi.id)));


ALTER VIEW public.segment_vector_details OWNER TO wy;

--
-- Name: subsc; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.subsc (
    id bigint NOT NULL,
    projectid integer,
    piid integer
);


ALTER TABLE public.subsc OWNER TO wy;

--
-- Name: subsc_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.subsc_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.subsc_id_seq OWNER TO wy;

--
-- Name: subsc_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.subsc_id_seq OWNED BY public.subsc.id;


--
-- Name: urllink; Type: TABLE; Schema: public; Owner: wy
--

CREATE TABLE public.urllink (
    id bigint NOT NULL,
    subject character varying(200),
    linkstr character varying(200),
    projectid integer,
    ordernum integer
);


ALTER TABLE public.urllink OWNER TO wy;

--
-- Name: urllink_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.urllink_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.urllink_id_seq OWNER TO wy;

--
-- Name: urllink_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.urllink_id_seq OWNED BY public.urllink.id;


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: wy
--

CREATE SEQUENCE public.users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO wy;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: wy
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: article_vectors id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.article_vectors ALTER COLUMN id SET DEFAULT nextval('public.article_vectors_id_seq'::regclass);


--
-- Name: attachment id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.attachment ALTER COLUMN id SET DEFAULT nextval('public.attachment_id_seq'::regclass);


--
-- Name: comment_vectors id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.comment_vectors ALTER COLUMN id SET DEFAULT nextval('public.comment_vectors_id_seq'::regclass);


--
-- Name: content_segment_vectors id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.content_segment_vectors ALTER COLUMN id SET DEFAULT nextval('public.content_segment_vectors_id_seq'::regclass);


--
-- Name: folders id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.folders ALTER COLUMN id SET DEFAULT nextval('public.folders_id_seq'::regclass);


--
-- Name: forumlist id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.forumlist ALTER COLUMN id SET DEFAULT nextval('public.forumlist_id_seq'::regclass);


--
-- Name: glovar id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.glovar ALTER COLUMN id SET DEFAULT nextval('public.glovar_id_seq'::regclass);


--
-- Name: iptable id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.iptable ALTER COLUMN id SET DEFAULT nextval('public.iptable_id_seq'::regclass);


--
-- Name: levels id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.levels ALTER COLUMN id SET DEFAULT nextval('public.levels_id_seq'::regclass);


--
-- Name: point_logs id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.point_logs ALTER COLUMN id SET DEFAULT nextval('public.point_logs_id_seq'::regclass);


--
-- Name: post id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.post ALTER COLUMN id SET DEFAULT nextval('public.post_id_seq'::regclass);


--
-- Name: project id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.project ALTER COLUMN id SET DEFAULT nextval('public.project_id_seq'::regclass);


--
-- Name: projectitem id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.projectitem ALTER COLUMN id SET DEFAULT nextval('public.projectitem_id_seq'::regclass);


--
-- Name: regkey id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.regkey ALTER COLUMN id SET DEFAULT nextval('public.regkey_id_seq'::regclass);


--
-- Name: relation id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.relation ALTER COLUMN id SET DEFAULT nextval('public.relation_id_seq'::regclass);


--
-- Name: subsc id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.subsc ALTER COLUMN id SET DEFAULT nextval('public.subsc_id_seq'::regclass);


--
-- Name: urllink id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.urllink ALTER COLUMN id SET DEFAULT nextval('public.urllink_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: article_vectors; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.article_vectors (id, projectitem_id, title_vector, title_text, content_vector, content_text, segment_count, vectorization_method, total_text_length, max_segment_length, aggregation_weights, overlap_strategy, window_size, step_size, avg_confidence, key_segment_ratio, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: attachment; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.attachment (id, parentid, amtype, comment, linkstr, createtime, updatetime) FROM stdin;
\.


--
-- Data for Name: comment_vectors; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.comment_vectors (id, post_id, title_vector, content_vector, title_text, content_text, segment_count, vectorization_method, total_text_length, max_segment_length, avg_confidence, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: content_segment_vectors; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.content_segment_vectors (id, article_vector_id, segment_index, segment_hash, segment_text, segment_vector, segment_length, token_count, word_count, start_char_pos, end_char_pos, start_token_pos, end_token_pos, prev_overlap_chars, next_overlap_chars, overlap_ratio, confidence_score, semantic_density, keyword_density, is_key_segment, segment_type, contains_title, created_at) FROM stdin;
\.


--
-- Data for Name: folders; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.folders (id, name, comment, parent, subitemcount, postcount, recordcount, projectid, ordernum) FROM stdin;
\.


--
-- Data for Name: forumlist; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.forumlist (id, name, comment, artcount) FROM stdin;
\.


--
-- Data for Name: glovar; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.glovar (id, varname, varvalue) FROM stdin;
\.


--
-- Data for Name: iptable; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.iptable (id, ip, createtime, state) FROM stdin;
\.


--
-- Data for Name: levels; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.levels (id, name) FROM stdin;
\.


--
-- Data for Name: point_logs; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.point_logs (id, user_id, points, source, log_date, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: post; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.post (id, folderid, rootid, userid, subject, content, size, status, hits, posttime, lastreplytime, lastreplyid, projectitemid, replycount, userip) FROM stdin;
\.


--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.project (id, name, comment, recordcount, accesscount, userid, folderid, createtime, state, lastitem, updatetime, commentcount) FROM stdin;
\.


--
-- Data for Name: projectitem; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.projectitem (id, projectid, name, comment, itemtype, itemsize, attachment, linkstr, userid, accesscount, updatetime, commentcount, createtime, folderid, lastmodifytime, status, allowpost) FROM stdin;
\.


--
-- Data for Name: regkey; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.regkey (id, name, ownerid, userid, status, createtime) FROM stdin;
\.


--
-- Data for Name: relation; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.relation (id, projectid, objectid, created, acttype) FROM stdin;
\.


--
-- Data for Name: subsc; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.subsc (id, projectid, piid) FROM stdin;
\.


--
-- Data for Name: urllink; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.urllink (id, subject, linkstr, projectid, ordernum) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: wy
--

COPY public.users (id, name, password, state, email, regtime, iplog, projectid, point, lastupdate, intropiid) FROM stdin;
1	admin                                             	$2b$12$xzCWfOXibxvyvGde/Y9iIeSe9V1YYEBa.PiUn6asHgNPO.ggsVTsa	10	                                                  	2025-10-14 21:52:07.592491	172.29.32.1    	\N	0	2025-10-14 13:52:27.510202	0
\.


--
-- Name: article_vectors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.article_vectors_id_seq', 1, false);


--
-- Name: attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.attachment_id_seq', 1, false);


--
-- Name: comment_vectors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.comment_vectors_id_seq', 1, false);


--
-- Name: content_segment_vectors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.content_segment_vectors_id_seq', 1, false);


--
-- Name: folders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.folders_id_seq', 1, false);


--
-- Name: forumlist_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.forumlist_id_seq', 1, false);


--
-- Name: glovar_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.glovar_id_seq', 1, false);


--
-- Name: iptable_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.iptable_id_seq', 1, false);


--
-- Name: levels_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.levels_id_seq', 1, false);


--
-- Name: point_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.point_logs_id_seq', 1, false);


--
-- Name: post_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.post_id_seq', 1, false);


--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.project_id_seq', 1, false);


--
-- Name: projectitem_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.projectitem_id_seq', 1, false);


--
-- Name: regkey_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.regkey_id_seq', 1, false);


--
-- Name: relation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.relation_id_seq', 1, false);


--
-- Name: subsc_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.subsc_id_seq', 1, false);


--
-- Name: urllink_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.urllink_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: wy
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: article_vectors article_vectors_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.article_vectors
    ADD CONSTRAINT article_vectors_pkey PRIMARY KEY (id);


--
-- Name: article_vectors article_vectors_projectitem_id_key; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.article_vectors
    ADD CONSTRAINT article_vectors_projectitem_id_key UNIQUE (projectitem_id);


--
-- Name: attachment attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.attachment
    ADD CONSTRAINT attachment_pkey PRIMARY KEY (id);


--
-- Name: comment_vectors comment_vectors_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.comment_vectors
    ADD CONSTRAINT comment_vectors_pkey PRIMARY KEY (id);


--
-- Name: comment_vectors comment_vectors_post_id_key; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.comment_vectors
    ADD CONSTRAINT comment_vectors_post_id_key UNIQUE (post_id);


--
-- Name: content_segment_vectors content_segment_vectors_article_vector_id_segment_index_key; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.content_segment_vectors
    ADD CONSTRAINT content_segment_vectors_article_vector_id_segment_index_key UNIQUE (article_vector_id, segment_index);


--
-- Name: content_segment_vectors content_segment_vectors_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.content_segment_vectors
    ADD CONSTRAINT content_segment_vectors_pkey PRIMARY KEY (id);


--
-- Name: folders folders_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.folders
    ADD CONSTRAINT folders_pkey PRIMARY KEY (id);


--
-- Name: forumlist forumlist_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.forumlist
    ADD CONSTRAINT forumlist_pkey PRIMARY KEY (id);


--
-- Name: glovar glovar_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.glovar
    ADD CONSTRAINT glovar_pkey PRIMARY KEY (id);


--
-- Name: iptable iptable_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.iptable
    ADD CONSTRAINT iptable_pkey PRIMARY KEY (id);


--
-- Name: levels levels_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.levels
    ADD CONSTRAINT levels_pkey PRIMARY KEY (id);


--
-- Name: point_logs point_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.point_logs
    ADD CONSTRAINT point_logs_pkey PRIMARY KEY (id);


--
-- Name: post post_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.post
    ADD CONSTRAINT post_pkey PRIMARY KEY (id);


--
-- Name: project project_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: projectitem projectitem_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.projectitem
    ADD CONSTRAINT projectitem_pkey PRIMARY KEY (id);


--
-- Name: regkey regkey_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.regkey
    ADD CONSTRAINT regkey_pkey PRIMARY KEY (id);


--
-- Name: relation relation_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.relation
    ADD CONSTRAINT relation_pkey PRIMARY KEY (id);


--
-- Name: subsc subsc_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.subsc
    ADD CONSTRAINT subsc_pkey PRIMARY KEY (id);


--
-- Name: urllink urllink_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.urllink
    ADD CONSTRAINT urllink_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_article_vectors_content_ivfflat; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_article_vectors_content_ivfflat ON public.article_vectors USING ivfflat (content_vector public.vector_cosine_ops) WITH (lists='50');


--
-- Name: idx_article_vectors_created_at; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_article_vectors_created_at ON public.article_vectors USING btree (created_at);


--
-- Name: idx_article_vectors_projectitem_id; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_article_vectors_projectitem_id ON public.article_vectors USING btree (projectitem_id);


--
-- Name: idx_article_vectors_title_ivfflat; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_article_vectors_title_ivfflat ON public.article_vectors USING ivfflat (title_vector public.vector_cosine_ops) WITH (lists='50');


--
-- Name: idx_article_vectors_updated_at; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_article_vectors_updated_at ON public.article_vectors USING btree (updated_at);


--
-- Name: idx_attachment_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_attachment_createtime ON public.attachment USING btree (createtime);


--
-- Name: idx_attachment_parentid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_attachment_parentid ON public.attachment USING btree (parentid);


--
-- Name: idx_comment_vectors_content_ivfflat; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_comment_vectors_content_ivfflat ON public.comment_vectors USING ivfflat (content_vector public.vector_cosine_ops) WITH (lists='75');


--
-- Name: idx_comment_vectors_created_at; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_comment_vectors_created_at ON public.comment_vectors USING btree (created_at);


--
-- Name: idx_comment_vectors_post_id; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_comment_vectors_post_id ON public.comment_vectors USING btree (post_id);


--
-- Name: idx_comment_vectors_title_ivfflat; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_comment_vectors_title_ivfflat ON public.comment_vectors USING ivfflat (title_vector public.vector_cosine_ops) WITH (lists='75');


--
-- Name: idx_comment_vectors_updated_at; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_comment_vectors_updated_at ON public.comment_vectors USING btree (updated_at);


--
-- Name: idx_folders_projectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_folders_projectid ON public.folders USING btree (projectid);


--
-- Name: idx_folders_projectid_id; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_folders_projectid_id ON public.folders USING btree (projectid, id DESC);


--
-- Name: idx_glovar_varname; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_glovar_varname ON public.glovar USING btree (varname);


--
-- Name: idx_point_logs_log_date; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_point_logs_log_date ON public.point_logs USING btree (log_date);


--
-- Name: idx_point_logs_user_date; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_point_logs_user_date ON public.point_logs USING btree (user_id, log_date);


--
-- Name: idx_point_logs_user_id; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_point_logs_user_id ON public.point_logs USING btree (user_id);


--
-- Name: idx_post_guestbook_main; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_guestbook_main ON public.post USING btree (projectitemid, rootid, posttime DESC) WHERE ((projectitemid = 0) AND (rootid = 0));


--
-- Name: idx_post_guestbook_replies; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_guestbook_replies ON public.post USING btree (projectitemid, rootid, posttime) WHERE (projectitemid = 0);


--
-- Name: idx_post_posttime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_posttime ON public.post USING btree (posttime DESC);


--
-- Name: idx_post_projectitemid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_projectitemid ON public.post USING btree (projectitemid);


--
-- Name: idx_post_projectitemid_gt0_posttime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_projectitemid_gt0_posttime ON public.post USING btree (projectitemid, posttime DESC) WHERE (projectitemid > 0);


--
-- Name: idx_post_projectitemid_posttime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_projectitemid_posttime ON public.post USING btree (projectitemid, posttime DESC);


--
-- Name: idx_post_projectitemid_status_posttime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_projectitemid_status_posttime ON public.post USING btree (projectitemid, status, posttime DESC);


--
-- Name: idx_post_rootid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_rootid ON public.post USING btree (rootid);


--
-- Name: idx_post_rootid_posttime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_rootid_posttime ON public.post USING btree (rootid, posttime);


--
-- Name: idx_post_status; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_status ON public.post USING btree (status);


--
-- Name: idx_post_userid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_post_userid ON public.post USING btree (userid);


--
-- Name: idx_project_accesscount; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_accesscount ON public.project USING btree (accesscount DESC);


--
-- Name: idx_project_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_createtime ON public.project USING btree (createtime DESC);


--
-- Name: idx_project_state; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_state ON public.project USING btree (state);


--
-- Name: idx_project_state_accesscount; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_state_accesscount ON public.project USING btree (state, accesscount DESC);


--
-- Name: idx_project_state_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_state_createtime ON public.project USING btree (state, createtime DESC);


--
-- Name: idx_project_userid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_project_userid ON public.project USING btree (userid);


--
-- Name: idx_projectitem_accesscount; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_accesscount ON public.projectitem USING btree (accesscount DESC);


--
-- Name: idx_projectitem_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_createtime ON public.projectitem USING btree (createtime DESC);


--
-- Name: idx_projectitem_folderid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_folderid ON public.projectitem USING btree (folderid);


--
-- Name: idx_projectitem_projectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_projectid ON public.projectitem USING btree (projectid);


--
-- Name: idx_projectitem_projectid_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_projectid_createtime ON public.projectitem USING btree (projectid, createtime DESC);


--
-- Name: idx_projectitem_projectid_folderid_status; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_projectid_folderid_status ON public.projectitem USING btree (projectid, folderid, status);


--
-- Name: idx_projectitem_projectid_status; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_projectid_status ON public.projectitem USING btree (projectid, status);


--
-- Name: idx_projectitem_projectid_status_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_projectid_status_createtime ON public.projectitem USING btree (projectid, status, createtime DESC);


--
-- Name: idx_projectitem_status; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_status ON public.projectitem USING btree (status);


--
-- Name: idx_projectitem_status_createtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_status_createtime ON public.projectitem USING btree (status, createtime DESC);


--
-- Name: idx_projectitem_userid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_projectitem_userid ON public.projectitem USING btree (userid);


--
-- Name: idx_relation_acttype; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_acttype ON public.relation USING btree (acttype);


--
-- Name: idx_relation_objectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_objectid ON public.relation USING btree (objectid);


--
-- Name: idx_relation_objectid_acttype; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_objectid_acttype ON public.relation USING btree (objectid, acttype);


--
-- Name: idx_relation_projectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_projectid ON public.relation USING btree (projectid);


--
-- Name: idx_relation_projectid_acttype; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_projectid_acttype ON public.relation USING btree (projectid, acttype);


--
-- Name: idx_relation_projectid_acttype_created; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_relation_projectid_acttype_created ON public.relation USING btree (projectid, acttype, created DESC);


--
-- Name: idx_segment_vectors_article_id; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_segment_vectors_article_id ON public.content_segment_vectors USING btree (article_vector_id);


--
-- Name: idx_segment_vectors_created_at; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_segment_vectors_created_at ON public.content_segment_vectors USING btree (created_at);


--
-- Name: idx_segment_vectors_key_segment; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_segment_vectors_key_segment ON public.content_segment_vectors USING btree (is_key_segment) WHERE (is_key_segment = true);


--
-- Name: idx_segment_vectors_segment_index; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_segment_vectors_segment_index ON public.content_segment_vectors USING btree (article_vector_id, segment_index);


--
-- Name: idx_segment_vectors_vector_ivfflat; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_segment_vectors_vector_ivfflat ON public.content_segment_vectors USING ivfflat (segment_vector public.vector_cosine_ops) WITH (lists='500');


--
-- Name: idx_subsc_piid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_subsc_piid ON public.subsc USING btree (piid);


--
-- Name: idx_subsc_projectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_subsc_projectid ON public.subsc USING btree (projectid);


--
-- Name: idx_subsc_projectid_piid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_subsc_projectid_piid ON public.subsc USING btree (projectid, piid);


--
-- Name: idx_urllink_ordernum; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_urllink_ordernum ON public.urllink USING btree (ordernum);


--
-- Name: idx_urllink_projectid; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_urllink_projectid ON public.urllink USING btree (projectid);


--
-- Name: idx_urllink_projectid_ordernum; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_urllink_projectid_ordernum ON public.urllink USING btree (projectid, ordernum);


--
-- Name: idx_users_email; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_email ON public.users USING btree (email);


--
-- Name: idx_users_name; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_name ON public.users USING btree (name);


--
-- Name: idx_users_name_lower; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_name_lower ON public.users USING btree (lower((name)::text));


--
-- Name: idx_users_point; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_point ON public.users USING btree (point DESC);


--
-- Name: idx_users_regtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_regtime ON public.users USING btree (regtime DESC);


--
-- Name: idx_users_state; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_state ON public.users USING btree (state);


--
-- Name: idx_users_state_point; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_state_point ON public.users USING btree (state, point DESC);


--
-- Name: idx_users_state_regtime; Type: INDEX; Schema: public; Owner: wy
--

CREATE INDEX idx_users_state_regtime ON public.users USING btree (state, regtime DESC);


--
-- Name: article_vectors trigger_update_article_vectors_updated_at; Type: TRIGGER; Schema: public; Owner: wy
--

CREATE TRIGGER trigger_update_article_vectors_updated_at BEFORE UPDATE ON public.article_vectors FOR EACH ROW EXECUTE FUNCTION public.update_article_vectors_updated_at();


--
-- Name: comment_vectors trigger_update_comment_vectors_updated_at; Type: TRIGGER; Schema: public; Owner: wy
--

CREATE TRIGGER trigger_update_comment_vectors_updated_at BEFORE UPDATE ON public.comment_vectors FOR EACH ROW EXECUTE FUNCTION public.update_comment_vectors_updated_at();


--
-- Name: article_vectors article_vectors_projectitem_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.article_vectors
    ADD CONSTRAINT article_vectors_projectitem_id_fkey FOREIGN KEY (projectitem_id) REFERENCES public.projectitem(id) ON DELETE CASCADE;


--
-- Name: comment_vectors comment_vectors_post_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.comment_vectors
    ADD CONSTRAINT comment_vectors_post_id_fkey FOREIGN KEY (post_id) REFERENCES public.post(id) ON DELETE CASCADE;


--
-- Name: content_segment_vectors content_segment_vectors_article_vector_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.content_segment_vectors
    ADD CONSTRAINT content_segment_vectors_article_vector_id_fkey FOREIGN KEY (article_vector_id) REFERENCES public.article_vectors(id) ON DELETE CASCADE;


--
-- Name: point_logs fk_point_logs_user_id; Type: FK CONSTRAINT; Schema: public; Owner: wy
--

ALTER TABLE ONLY public.point_logs
    ADD CONSTRAINT fk_point_logs_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

