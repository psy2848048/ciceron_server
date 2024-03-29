﻿--DROP SCHEMA CICERON cascade;
CREATE SCHEMA CICERON;
SET SCHEMA 'CICERON';

CREATE TABLE CICERON.D_USERS (
    id INT not null,
    email varchar(100) not null,
    name varchar(100) not null,
    mother_language_id INT not null, -- D_LANGUAGES
    is_translator BOOLEAN,
    is_admin BOOLEAN,
    other_language_list_id INT,
    profile_pic_path varchar(300),
    numOfRequestPending INT,
    numOfRequestOngoing INT,
    numOfRequestCompleted INT,
    numOfTranslationPending INT,
    numOfTranslationOngoing INT,
    numOfTranslationCompleted INT,
    badgeList_id INT, -- D_AWARDED_BADGES
    profile_text varchar(1000),
    trans_request_state INT,
    nationality INT,
    residence INT,
    return_rate REAL,
    member_since TIMESTAMPTZ,
    
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX useremail ON CICERON.D_USERS (email);

CREATE TABLE CICERON.F_USER_PROFILE_PIC (
    user_id INT,
    filename varchar(300),
    bin bytea,

    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_D_USERS;

CREATE TABLE CICERON.D_FACEBOOK_USERS (
    id INT,
    email varchar(200),
    real_id INT,
    
    PRIMARY KEY (id),
    FOREIGN KEY (real_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_D_FACEBOOK_USERS;

CREATE TABLE CICERON.PASSWORDS (
    user_id INT, -- D_USERS
    hashed_pass varchar(128),
    
    PRIMARY KEY(user_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE TABLE CICERON.D_LANGUAGES (
    id INT,
    text varchar(100),
    google_code varchar(10),
    yandex_code varchar(10),
    bing_code varchar(10),
    
    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_LANGUAGES;

INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Korean', 'ko', 'ko', 'ko');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'English(USA)', 'en', 'en', 'en');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'English(UK)', 'en', 'en', 'en');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Chinese(Mandarin)', 'zh-CN', 'zh', 'zh-CHS');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Chinese(Cantonese)', 'zh-CN', 'zh', 'zh-CHS');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Thai', 'th', 'th', 'th');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Chinese(Taiwanese)', 'zh-TW', null, 'zh-CHT');

INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Japanese', 'ja', 'ja', 'ja');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Spanish', 'es', 'es', 'es');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Portuguese', 'pt', 'pt', 'pt');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Vietnamese', 'vi', 'vi', 'vi');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'German', 'de', 'de', 'de');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'French', 'fr', 'fr', 'fr');

CREATE TABLE CICERON.D_TRANSLATABLE_LANGUAGES (
    id INT,
    user_id INT, -- D_USERS
    language_id INT, -- D_LANGUAGES
    
    PRIMARY KEY (id),
    FOREIGN KEY (language_id) REFERENCES CICERON.D_LANGUAGES (id)
);

CREATE SEQUENCE CICERON.SEQ_D_TRANSLATABLE_LANGUAGES;

CREATE TABLE CICERON.D_NATIONS (
    id INT,
    name varchar(100),
    
    PRIMARY KEY (id)
);

INSERT INTO CICERON.D_NATIONS VALUES (1, 'Korea');
INSERT INTO CICERON.D_NATIONS VALUES (2, 'USA');
INSERT INTO CICERON.D_NATIONS VALUES (3, 'UK');
INSERT INTO CICERON.D_NATIONS VALUES (4, 'China(Mainland)');
INSERT INTO CICERON.D_NATIONS VALUES (5, 'China(Hong Kong, Macao)');
INSERT INTO CICERON.D_NATIONS VALUES (6, 'Thailand');
INSERT INTO CICERON.D_NATIONS VALUES (7, 'China(Taiwan)');

INSERT INTO CICERON.D_NATIONS VALUES (8, 'Japanese');
INSERT INTO CICERON.D_NATIONS VALUES (9, 'Spanish');
INSERT INTO CICERON.D_NATIONS VALUES (10, 'Portuguese');
INSERT INTO CICERON.D_NATIONS VALUES (11, 'Vietnamese');
INSERT INTO CICERON.D_NATIONS VALUES (12, 'German');
INSERT INTO CICERON.D_NATIONS VALUES (13, 'French');

CREATE TABLE CICERON.D_RESIDENCE (
    id INT,
    name varchar(100),
    
    PRIMARY KEY(id)
);

INSERT INTO CICERON.D_RESIDENCE VALUES (0, 'Korea');
INSERT INTO CICERON.D_RESIDENCE VALUES (1, 'USA');
INSERT INTO CICERON.D_RESIDENCE VALUES (2, 'UK');
INSERT INTO CICERON.D_RESIDENCE VALUES (3, 'China(Mainland)');
INSERT INTO CICERON.D_RESIDENCE VALUES (4, 'China(Hong Kong, Macao)');
INSERT INTO CICERON.D_RESIDENCE VALUES (5, 'Thailand');

CREATE TABLE CICERON.D_KEYWORDS (
    id INT,
    text varchar(100),
    
    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_D_KEYWORDS;

CREATE TABLE CICERON.D_USER_KEYWORDS (
    user_id INT,
    keyword_id INT,
    
    PRIMARY KEY (user_id, keyword_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (keyword_id) REFERENCES CICERON.D_KEYWORDS(id)
);

CREATE TABLE CICERON.D_FORMATS (
    id INT,
    text varchar(200),
    
    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_FORMATS;

CREATE TABLE CICERON.D_SUBJECTS(
    id INT,
    text varchar(200),
    
    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_SUBJECTS;

CREATE TABLE CICERON.F_REQUESTS (
    id INT,
    client_user_id INT not null, -- D_USERS
    original_lang_id INT not null, -- D_LANGUAGES
    target_lang_id INT not null, -- D_LANGUAGES
    isSos BOOLEAN not null,
    status_id INT not null, -- 0: pending, 1: ongoing, 2: completed
    format_id INT, -- D_FORMATS
    subject_id INT, -- D_SUBJECTS
    queue_id INT, -- Useless
    ongoing_worker_id INT, -- D_USERS
    is_text BOOLEAN not null,
    text_id INT, -- D_REQUEST_TEXTS
    is_photo BOOLEAN not null,
    photo_id INT, -- D_REQUEST_PHOTOS
    is_file BOOLEAN not null,
    file_id INT, -- D_REQUEST_FILES
    is_sound BOOLEAN not null,
    sound_id INT, -- D_REQUEST_SOUNDS
    client_completed_group_id INT, -- D_CLIENT_COMPLETED_GROUPS
    translator_completed_group_id INT, -- D_TRANSLATOR_COMPLETED_GROUPS
    client_title_id INT, -- D_CLIENT_COMPLETED_REQUEST_TITLES
    translator_title_id INT, -- D_TRANSLATOR_COMPLETED_REQUEST_TITLES
    is_paid BOOLEAN not null,
    registered_time TIMESTAMPTZ,
    due_time TIMESTAMPTZ,
    expected_time TIMESTAMPTZ,
    submitted_time TIMESTAMPTZ,
    points REAL,
    context_id INT, -- D_CONTEXTS
    comment_id INT, -- D_COMMENTS
    tone_id INT, -- D_TONES
    translatedText_id INT, -- D_TRANSLATED_TEXT
    feedback_score INT,
    start_translating_time TIMESTAMPTZ,
    is_need_additional_points BOOLEAN,
    additional_points REAL,
    is_additional_points_paid BOOLEAN,

    is_i18n BOOLEAN,
    is_movie BOOLEAN,
    is_docx BOOLEAN,
    is_public BOOLEAN,

    is_groupRequest BOOLEAN,
    resell_price REAL,
    is_copyright_checked BOOLEAN,
    number_of_member_in_group INT,
    
    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_F_REQUESTS;

CREATE TABLE CICERON.D_REQUEST_TEXTS (
    id INT,
    paragragh_seq,
    sentence_seq,
    path varchar(200),
    text TEXT,
    hit INT,
    translation_id INT,
    is_sent_to_machine boolean,
    original_lang_id INT,
    target_lang_id INT,

    PRIMARY KEY (id, paragragh_seq, sentence_seq)
);
CREATE INDEX sentence ON CICERON.D_REQUEST_TEXTS (text);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_TEXTS;

--CREATE TABLE CICERON.D_REQUEST_PHOTOS (
--    id INT,
--    path varchar(300),
--    bin BYTEA,
--
--    PRIMARY KEY(id)
--);
--
--CREATE SEQUENCE CICERON.SEQ_D_REQUEST_PHOTOS;

CREATE TABLE CICERON.D_REQUEST_FILES (
    id INT,
    path varchar(300),
    bin BYTEA,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_FILES;

CREATE TABLE CICERON.D_TRANSLATED_FILES (
    id INT,
    request_id INT,
    path varchar(300),
    bin BYTEA,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_TRANSLATED_FILES;

CREATE TABLE CICERON.D_UNORGANIZED_TRANSLATED_RESULT(
    id INT,
    request_id INT,
    file_id INT,
    file_name VARCHAR(200),
    translated_text TEXT,
    translated_file BYTEA,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_UNORGANIZED_TRANSLATED_RESULT;

--CREATE TABLE CICERON.D_REQUEST_SOUNDS (
--    id INT,
--    path varchar(300),
--    bin BYTEA,
--
--    PRIMARY KEY (id)
--);
--
--CREATE SEQUENCE CICERON.SEQ_D_REQUEST_SOUNDS;

CREATE TABLE CICERON.D_CLIENT_COMPLETED_GROUPS (
    id INT,
    user_id INT, -- D_USERS
    text varchar(30),

    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_D_CLIENT_COMPLETED_GROUPS;

CREATE TABLE CICERON.D_TRANSLATOR_COMPLETED_GROUPS (
    id INT,
    user_id INT, -- D_USERS
    text varchar(30),

    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_D_TRANSLATOR_COMPLETED_GROUPS;

CREATE TABLE CICERON.D_CLIENT_COMPLETED_REQUEST_TITLES (
    id INT,
    text varchar(200),

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_CLIENT_COMPLETED_REQUEST_TITLES;

CREATE TABLE CICERON.D_TRANSLATOR_COMPLETED_REQUEST_TITLES (
    id INT,
    text varchar(200),

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_TRANSLATOR_COMPLETED_REQUEST_TITLES;

CREATE TABLE CICERON.D_CONTEXTS (
    id INT,
    text TEXT,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_CONTEXTS;

CREATE TABLE CICERON.D_COMMENTS (
    id INT,
    text TEXT,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_COMMENTS;

CREATE TABLE CICERON.D_TONES (
    id INT,
    text TEXT,

    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_D_TONES;

CREATE TABLE CICERON.D_QUEUE_LISTS (
    id INT,
    request_id INT, -- REQUEST_ID from F_REQUESTS
    user_id INT, -- D_USERS
    nego_price REAL,
    PRIMARY KEY (id, request_id, user_id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS
);

CREATE SEQUENCE CICERON.SEQ_D_QUEUE_LISTS;

CREATE TABLE CICERON.D_TRANSLATED_TEXT(
    id INT,
    paragragh_seq INT,
    sentence_seq INT,
    path varchar(300),
    google_result TEXT,
    yandex_result TEXT,
    bing_result TEXT,
    text TEXT,

    PRIMARY KEY (id, paragragh_seq, sentence_seq)
);

CREATE SEQUENCE CICERON.SEQ_D_TRANSLATED_TEXT;

CREATE TABLE CICERON.D_BADGES (
    id INT,
    text varchar(100),

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_BADGES;

CREATE TABLE CICERON.D_AWARDED_BADGES (
    id INT,
    user_id INT,  -- badgeList_id from D_USERS
    badge_id INT, -- D_BADGES

    PRIMARY KEY (id, user_id, badge_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (badge_id) REFERENCES CICERON.D_BADGES (id)
);

CREATE SEQUENCE CICERON.SEQ_D_AWARDED_BADGES;

CREATE TABLE CICERON.D_MACHINE_OSS(
    id INT,
    text varchar(30),

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_MACHINE_OSS;

INSERT INTO CICERON.D_MACHINE_OSS VALUES (nextval('CICERON.SEQ_D_MACHINE_OSS'), 'android_phone');
INSERT INTO CICERON.D_MACHINE_OSS VALUES (nextval('CICERON.SEQ_D_MACHINE_OSS'), 'android_tab');
INSERT INTO CICERON.D_MACHINE_OSS VALUES (nextval('CICERON.SEQ_D_MACHINE_OSS'), 'ios_phone');
INSERT INTO CICERON.D_MACHINE_OSS VALUES (nextval('CICERON.SEQ_D_MACHINE_OSS'), 'ios_tab');

CREATE TABLE CICERON.D_MACHINES (
    id INT,
    user_id INT not null,
    os_id INT not null, -- D_MACHINE_OSS
    is_push_allowed BOOLEAN,
    reg_key TEXT,

    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (os_id) REFERENCES CICERON.D_MACHINE_OSS (id)
);

CREATE SEQUENCE CICERON.SEQ_D_MACHINES;

CREATE TABLE CICERON.EMERGENCY_CODE (
    user_id INT, -- D_USERS
    code varchar(128),
    
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE TABLE CICERON.REVENUE (
    -- 번역가 계좌
    id INT, -- D_USER
    amount REAL,

    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES CICERON.D_USERS (id)
);

CREATE TABLE CICERON.RETURN_POINT (
    -- 의뢰인 포인트&미환급금
    id INT,
    amount REAL,

    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES CICERON.D_USERS (id)
);

CREATE TABLE CICERON.F_PAYMENT_INFO (
    id INT,
    product VARCHAR(20),
    transaction_type VARCHAR(10),
    request_id INT,
    user_id INT,
    payed_platform varchar(20),
    order_no VARCHAR(100),
    amount DECIMAL(10,2),
    transaction_time TIMESTAMPTZ,
    
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);
CREATE INDEX order_no ON CICERON.F_PAYMENT_INFO (order_no);

CREATE SEQUENCE CICERON.SEQ_F_PAYMENT_INFO;

CREATE VIEW CICERON.V_REQUESTS as
  SELECT distinct
    -- Client
    fact.id request_id, --0
    fact.client_user_id client_user_id, --1
    user_client.email client_email, --2
    user_client.name client_name, --3
    user_client.profile_pic_path client_profile_pic_path, --4
    -- Translator
    fact.ongoing_worker_id ongoing_worker_id, --5
    user_translator.email translator_email, --6
    user_translator.name translator_name, --7
    user_translator.profile_pic_path translator_profile_pic_path, --8
    user_translator.numOfTranslationPending numOfTranslationPending, --9
    user_translator.numOfTranslationOngoing numOfTranslationOngoing, --10
    user_translator.numOfTranslationCompleted numOfTranslationCompleted, --11
    user_translator.badgeList_id translator_badgeList_id, --12
    -- Language
    fact.original_lang_id original_lang_id, --13
    original_lang.text original_lang, --14
    fact.target_lang_id target_lang_id, --15
    target_lang.text target_lang, --16
    -- Request status
    fact.isSos isSos, --17
    fact.status_id status_id, --18
    fact.format_id format_id, --19
    format.text format, --20
    fact.subject_id subject_id, --21
    subject.text subject, --22
    fact.queue_id queue_id, --23

    fact.registered_time registered_time, --24
    fact.expected_time expected_time, --25
    fact.submitted_time submitted_time, --26
    fact.due_time due_time, --27
    fact.points points, --28
    -- Request type
    fact.is_text is_text, --29
    fact.text_id text_id, --30
    fact.is_photo is_photo, --31
    fact.photo_id photo_id, --32
    fact.is_file is_file, --33
    fact.file_id file_id, --34
    fact.is_sound is_sound, --35
    fact.sound_id sound_id, --36
    -- Request more info
    fact.context_id context_id, --37
    contexts.text context, --38
    fact.comment_id comment_id, --39
    comments.text "COMMENT", --40
    fact.tone_id tone_id, --41
    tones.text tone, --42
    -- Grouping
    fact.client_completed_group_id client_completed_group_id, --43
    client_groups.text client_completed_group, --44
    fact.client_title_id client_title_id, --45
    client_titles.text client_title, --46
    fact.translator_completed_group_id translator_completed_group_id, --47
    translator_groups.text translator_completed_group, --48
    fact.translator_title_id translator_title_id, --49
    translator_title.text translator_title, --50
    -- Result
    fact.translatedText_id translatedText_id, --51
    result.path translatedText, --52
    fact.is_paid is_paid, --53
    fact.feedback_score feedback_score, --54

    fact.start_translating_time start_translating_time, --55
    fact.is_need_additional_points is_need_additional_points, --56
    fact.additional_points additional_points, --57
    fact.is_additional_points_paid is_additional_points_paid, -- 58

    fact.is_i18n is_i18n, -- 59
    fact.is_movie is_movie, -- 60
    fact.is_groupRequest is_groupRequest, --61

    fact.is_docx is_docx, -- 62
    fact.is_public is_public, --63
    fact.resell_price, --64
    fact.is_copyright_checked is_copyright_checked, --65
    fact.number_of_member_in_group number_of_member_in_group, --66

    group_request.members requested_member,  -- 67
    copyright.is_confirmed is_confirmed      -- 68

  FROM
    CICERON.F_REQUESTS fact
  LEFT OUTER JOIN CICERON.D_USERS user_client ON fact.client_user_id = user_client.id
  LEFT OUTER JOIN CICERON.D_USERS user_translator ON fact.ongoing_worker_id = user_translator.id
  LEFT OUTER JOIN CICERON.D_LANGUAGES original_lang ON fact.original_lang_id = original_lang.id
  LEFT OUTER JOIN CICERON.D_LANGUAGES target_lang ON fact.target_lang_id = target_lang.id
  LEFT OUTER JOIN CICERON.D_FORMATS format ON fact.format_id = format.id
  LEFT OUTER JOIN CICERON.D_SUBJECTS subject ON fact.subject_id = subject.id
  LEFT OUTER JOIN CICERON.D_CONTEXTS contexts ON fact.context_id = contexts.id
  LEFT OUTER JOIN CICERON.D_COMMENTS comments ON fact.comment_id = comments.id
  LEFT OUTER JOIN CICERON.D_TONES tones ON fact.tone_id = tones.id
  LEFT OUTER JOIN CICERON.D_CLIENT_COMPLETED_GROUPS client_groups
             ON fact.client_completed_group_id = client_groups.id
  LEFT OUTER JOIN CICERON.D_TRANSLATOR_COMPLETED_GROUPS translator_groups
             ON fact.translator_completed_group_id = translator_groups.id
  LEFT OUTER JOIN CICERON.D_CLIENT_COMPLETED_REQUEST_TITLES client_titles
             ON fact.client_title_id = client_titles.id
  LEFT OUTER JOIN CICERON.D_TRANSLATOR_COMPLETED_REQUEST_TITLES translator_title
             ON fact.translator_title_id = translator_title.id
  LEFT OUTER JOIN CICERON.D_TRANSLATED_TEXT result
             ON fact.translatedText_id = result.id
  LEFT OUTER JOIN 
                (SELECT request_id, count(*) members
                FROM CICERON.F_GROUP_REQUESTS_USERS
                WHERE is_paid = true
                GROUP BY request_id) group_request
             ON fact.id = group_request.request_id
  LEFT OUTER JOIN CICERON.F_PUBLIC_REQUESTS_COPYRIGHT_CHECK copyright
             ON fact.id = copyright.request_id
            ;

CREATE VIEW CICERON.V_TRANSLATABLE_LANGUAGES as
  SELECT
    fact.id id,
    fact.user_id user_id,
    users.email user_email,
    users.name user_name,
    fact.language_id translatable_language_id,
    languages.text translatable_language
  FROM
    CICERON.D_TRANSLATABLE_LANGUAGES fact
  LEFT OUTER JOIN CICERON.D_USERS users ON fact.user_id = users.id
  LEFT OUTER JOIN CICERON.D_LANGUAGES languages ON fact.language_id = languages.id;

CREATE VIEW CICERON.V_QUEUE_LISTS as
  SELECT
   fact.id id,
   fact.request_id request_id,
   fact.user_id user_id,
   users.email user_email,
   users.name user_name,
   users.mother_language_id mother_language_id, -- D_LANGUAGES
   users.is_translator is_translator,
   users.other_language_list_id other_language_list_id,
   users.profile_pic_path profile_pic_path,
   users.numOfRequestPending numOfRequestPending,
    users.numOfRequestOngoing numOfRequestOngoing,
    users.numOfRequestCompleted numOfRequestCompleted,
    users.numOfTranslationPending numOfTranslationPending,
   users.numOfTranslationOngoing numOfTranslationOngoing,
    users.numOfTranslationCompleted numOfTranslationCompleted,
    users.badgeList_id badgeList_id, -- D_AWARDED_BADGES
    users.profile_text profile_text,
   fact.nego_price nego_price
  FROM
    CICERON.D_QUEUE_LISTS fact
  LEFT OUTER JOIN CICERON.D_USERS users ON fact.user_id = users.id;

CREATE TABLE CICERON.TEMP_ACTIONS_LOG (
    id INT,
    user_id INT,
    lati REAL,
    longi REAL,
    method varchar(10),
    api varchar(300),
    log_time TIMESTAMPTZ,
    ip_address varchar(100),

    PRIMARY KEY (id)
);

CREATE TABLE CICERON.USER_ACTIONS (
    id INT,
    user_id INT,
    lati REAL,
    longi REAL,
    method varchar(10),
    api varchar(300),
    log_time TIMESTAMPTZ,
    ip_address varchar(100),

    PRIMARY KEY (id)
);
CREATE SEQUENCE CICERON.SEQ_USER_ACTIONS;

CREATE TABLE CICERON.BLACKLIST (
    id INT,
    user_id INT,
    ip_address varchar(20),
    time_from TIMESTAMPTZ,
    time_to TIMESTAMPTZ,

    PRIMARY KEY (id)
);
CREATE SEQUENCE CICERON.SEQ_BLACKLIST;

CREATE TABLE CICERON.RETURN_MONEY_BANK_ACCOUNT (
    id INT,
    order_no varchar(100),
    user_id INT,
    bank_name varchar(20),
    account_no varchar(50),
    request_time TIMESTAMPTZ,
    amount REAL,
    is_returned BOOLEAN,
    return_time TIMESTAMPTZ,

    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_RETURN_MONEY_BANK_ACCOUNT;

CREATE TABLE CICERON.D_NOTI_TYPE (
    id INT,
    text varchar(50),

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_NOTI_TYPE;

INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'new_request_alarm');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'enter_expected_time');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'your_request_is_rated');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'deadline_exceeded');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'due_time_extended');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'cancel_due_to_no_expectedDue');

INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'start_translating');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'check_expected_deadline');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'give_up_translation');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'no_expectedDue_go_to_stoa');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'finish_request');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'not_finish_request');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'no_translator_comes');

INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'youve_got_badge');
INSERT INTO CICERON.D_NOTI_TYPE VALUES (nextval('CICERON.SEQ_D_NOTI_TYPE'), 'paid_back');

CREATE TABLE CICERON.F_NOTIFICATION (
    id INT,
    user_id INT,
    noti_type_id INT,
    target_user_id INT,
    request_id INT,
    ts TIMESTAMPTZ,
    is_read BOOLEAN,
    is_mail_sent BOOLEAN,

    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (noti_type_id) REFERENCES CICERON.D_NOTI_TYPE (id),
    FOREIGN KEY (target_user_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id)
);
CREATE SEQUENCE CICERON.SEQ_F_NOTIFICATION;

CREATE VIEW CICERON.V_NOTIFICATION as
  SELECT
    fact.id id,
    fact.user_id user_id, --0
    users.email user_email, --1
    users.name user_name, --2
    fact.noti_type_id noti_type_id, --3
    noti.text noti_type, --4
    fact.request_id request_id, --5
    req.context context, --6
    req.registered_time registered_time, --7
    req.expected_time expected_time, --8
    req.submitted_time submitted_time, --9
    req.start_translating_time start_translating_time, --10
    req.due_time due_time, --11
    req.points points, --12
    fact.target_user_id target_user_id, --13
    users2.email target_user_email, --14
    users2.name target_user_name, --15
    users2.profile_pic_path target_profile_pic_path,  --16
    fact.ts ts, --17
    fact.is_read is_read, --18
    users.profile_pic_path user_profile_pic_path,
    req.status_id status_id,

    fact.is_mail_sent is_mail_sent

  FROM CICERON.F_NOTIFICATION fact
  LEFT OUTER JOIN CICERON.D_USERS users ON fact.user_id = users.id
  LEFT OUTER JOIN CICERON.D_USERS users2 ON fact.target_user_id = users2.id
  LEFT OUTER JOIN CICERON.D_NOTI_TYPE noti ON fact.noti_type_id = noti.id
  LEFT OUTER JOIN CICERON.V_REQUESTS req ON fact.request_id = req.request_id;

CREATE TABLE CICERON.PROMOTIONCODES_COMMON (
    id INT,
    text VARCHAR(10),
    benefitPoint REAL,
    expireTime TIMESTAMPTZ,
    
    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_PROMOTIONCODES_COMMON;

CREATE TABLE CICERON.USEDPROMOTION_COMMON (
    id INT,
    user_id INT,
    
    PRIMARY KEY(id, user_id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_USEDPROMOTION_COMMON;

CREATE TABLE CICERON.PROMOTIONCODES_USER (
    id INT,
    user_id INT,
    text VARCHAR(10),
    benefitPoint REAL,
    expireTime TIMESTAMPTZ,
    is_used BOOLEAN,
    
    PRIMARY KEY(id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_PROMOTIONCODES_USER;

CREATE TABLE CICERON.USER_DEFINED_DICTIONARY(
    id INT,
    meaning_id INT,
    request_id INT,
    language_id INT,
    category VARCHAR(20),
    word VARCHAR(100),
    added_user_id INT,
    added_ts TIMESTAMPTZ,

    PRIMARY KEY (id),
    UNIQUE (request_id, language_id, category, word, added_user_id),
    FOREIGN KEY (added_user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE INDEX request_id ON CICERON.USER_DEFINED_DICTIONARY (request_id);
CREATE INDEX meaning_id ON CICERON.USER_DEFINED_DICTIONARY (meaning_id);
CREATE INDEX word ON CICERON.USER_DEFINED_DICTIONARY (word);
CREATE INDEX added_user_id ON CICERON.USER_DEFINED_DICTIONARY (added_user_id);
CREATE SEQUENCE CICERON.SEQ_USER_DEFINED_DICTIONARY;
CREATE SEQUENCE CICERON.SEQ_USER_DEFINED_DICTIONARY_MEANING;

CREATE TABLE CICERON.CENTRAL_DICTIONARY(
    id INT,
    meaning_id INT,
    language_id INT,
    category VARCHAR(20),
    word VARCHAR(100),
    added_user_id INT,
    added_ts TIMESTAMPTZ,

    PRIMARY KEY (id),
    UNIQUE (language_id, category, word, added_user_id),
    FOREIGN KEY (added_user_id) REFERENCES CICERON.D_USERS (id)
);

CREATE INDEX meaning_id2 ON CICERON.CENTRAL_DICTIONARY (meaning_id);
CREATE INDEX word2 ON CICERON.CENTRAL_DICTIONARY (word);
CREATE INDEX added_user_id2 ON CICERON.CENTRAL_DICTIONARY (added_user_id);
CREATE SEQUENCE CICERON.SEQ_CENTRAL_DICTIONARY;
CREATE SEQUENCE CICERON.SEQ_CENTRAL_DICTIONARY_MEANING_ID;

CREATE TABLE CICERON.COMMENT_SENTENCE (
    request_id INT,
    paragraph_seq INT,
    sentence_seq INT,
    comment_string VARCHAR(5000),

    PRIMARY KEY (request_id, paragraph_seq, sentence_seq),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id)
);
CREATE INDEX request_id2 ON CICERON.COMMENT_SENTENCE (request_id);

CREATE TABLE CICERON.COMMENT_PARAGRAPH (
    request_id INT,
    paragraph_seq INT,
    comment_string VARCHAR(5000),

    PRIMARY KEY (request_id, paragraph_seq),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id)
);
CREATE INDEX request_id3 ON CICERON.COMMENT_PARAGRAPH (request_id);

CREATE TABLE CICERON.D_I18N_VARIABLE_NAMES (
    id INT,
    text VARCHAR(100),
    comment_string VARCHAR(5000),

    PRIMARY KEY (id)
);
CREATE SEQUENCE CICERON.SEQ_D_I18N_VARIABLE_NAMES;

CREATE TABLE CICERON.D_I18N_TEXTS (
    id INT,
    text TEXT,
    md5_checksum VARCHAR(40),
    hit_count INT,

    PRIMARY KEY (id)
);
CREATE SEQUENCE CICERON.SEQ_D_I18N_TEXTS;

CREATE TABLE CICERON.F_I18N_TEXT_MAPPINGS (
    id INT,
    variable_id INT,
    lang_id INT,
    paragraph_seq INT,
    sentence_seq INT,
    text_id INT,
    is_curated BOOLEAN,
    is_init_translated BOOLEAN,

    PRIMARY KEY (id),
    FOREIGN KEY (text_id) REFERENCES CICERON.D_I18N_TEXTS (id),
    FOREIGN KEY (variable_id) REFERENCES CICERON.D_I18N_VARIABLE_NAMES (id)
);
CREATE SEQUENCE CICERON.SEQ_F_I18N_TEXT_MAPPINGS;

CREATE TABLE CICERON.F_I18N_VALUES (
    id INT,
    request_id INT,
    variable_id INT,
    source_text_mapping_id INT,
    target_text_mapping_id INT,

    PRIMARY KEY (id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id),
    FOREIGN KEY (variable_id) REFERENCES CICERON.D_I18N_VARIABLE_NAMES (id),
    FOREIGN KEY (source_text_mapping_id) REFERENCES CICERON.F_I18N_TEXT_MAPPINGS (id),
    FOREIGN KEY (target_text_mapping_id) REFERENCES CICERON.F_I18N_TEXT_MAPPINGS (id)
);
CREATE SEQUENCE CICERON.SEQ_F_I18N_VALUES;

CREATE TABLE CICERON.F_GROUP_REQUESTS_USERS (
    id INT,
    request_id INT,
    user_id INT,
    is_paid BOOLEAN,
    payment_platform VARCHAR(30),
    transaction_id VARCHAR(100),
    complete_client_group_id INT,
    complete_client_title_id INT,

    PRIMARY KEY (id, request_id, user_id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);
CREATE SEQUENCE CICERON.SEQ_F_GROUP_REQUESTS_USERS;

CREATE TABLE CICERON.F_READ_PUBLIC_REQUESTS_USERS (
    id INT,
    request_id INT,
    user_id INT,
    is_paid BOOLEAN,
    payment_platform VARCHAR(30),
    transaction_id VARCHAR(100),
    complete_client_group_id INT,
    complete_client_title_id INT,

    PRIMARY KEY (id, request_id, user_id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id),
    FOREIGN KEY (user_id) REFERENCES CICERON.D_USERS (id)
);
CREATE SEQUENCE CICERON.SEQ_F_READ_PUBLIC_REQUESTS_USERS;

CREATE TABLE CICERON.F_PUBLIC_REQUESTS_COPYRIGHT_CHECK (
    id INT,
    request_id INT,
    is_confirmed BOOLEAN,
    file_bin BYTEA,

    PRIMARY KEY (id, request_id)
);
CREATE SEQUENCE CICERON.SEQ_F_PUBLIC_REQUESTS_COPYRIGHT_CHECK;

CREATE TABLE CICERON.INIT_TRANSLATION_TEMP (
    id INT,
    sentence VARCHAR(2000)
);
CREATE SEQUENCE CICERON.SEQ_INIT_TRANSLATION_TEMP;

CREATE TABLE CICERON. F_PRETRANSLATED_PROJECT (
    id int NOT NULL,
    original_resource_id int,
    original_lang_id int,
    format_id int,
    subject_id int,
    author varchar(127),
    register_timestamp timestamptz,
    cover_photo_filename varchar(255),
    cover_photo_binary bytea,

    PRIMARY KEY (id)
);
CREATE SEQUENCE CICERON.SEQ_F_PRETRANSLATED_PROJECT;

CREATE TABLE CICERON. F_PRETRANSLATED_RESOURCES (
    id int NOT NULL,
    project_id int,
    target_language_id int,
    theme varchar(255),
    description varchar(2047),
    tone_id int,
    read_permission_level int,
    price real,
    register_timestamp timestamptz,

    PRIMARY KEY (id)
)
;
CREATE SEQUENCE CICERON.SEQ_F_PRETRANSLATED_RESOURCES;

CREATE TABLE CICERON. F_PRETRANSLATED_RESULT_FILE (
    id int NOT NULL,
    project_id int,
    resource_id int,
    preview_permission int,
    file_name varchar(255),
    checksum varchar(255),
    file_binary bytea,

    PRIMARY KEY (id)
)
;
CREATE SEQUENCE CICERON.SEQ_F_PRETRANSLATED_RESULT_FILE;

CREATE TABLE CICERON. F_PRETRANSLATED_DOWNLOADED_USER (
    id int NOT NULL,
    resource_id int,
    is_user bool,
    email varchar(255),
    is_paid bool,
    is_sent bool,
    token varchar(255),
    is_downloaded bool,
    feedback_score INT,
    request_timestamp timestamptz,

    PRIMARY KEY (id)
)
;
CREATE SEQUENCE CICERON.SEQ_F_PRETRANSLATED_DOWNLOADED_USER;

CREATE TABLE CICERON. F_PRETRANSLATED_REQUESTER (
    requester_id int NOT NULL,
    resource_id int NOT NULL,
    project_id int,

    PRIMARY KEY (requester_id, resource_id)
)
;

CREATE TABLE CICERON. F_PRETRANSLATED_TRANSLATOR (
    translator_id int NOT NULL,
    resource_id int NOT NULL,
    project_id int,

    PRIMARY KEY (translator_id, resource_id)
)
;

CREATE VIEW CICERON.V_PRETRANSLATED_PROJECT AS
  SELECT
    fact.id,
    fact.original_resource_id,
    fact.original_lang_id,
    lang.text original_lang,
    resources.target_language_id,
    lang2.text target_language,
    fact.format_id,
    formats.text format,
    fact.subject_id,
    subjects.text subject,
    fact.author,
    fact.register_timestamp project_register_timestamp,
    resources.theme original_theme,
    resources.description,
    resources.register_timestamp resource_register_timestamp
  FROM CICERON. F_PRETRANSLATED_PROJECT fact
  LEFT OUTER JOIN CICERON.D_LANGUAGES lang
    ON fact.original_lang_id = lang.id
  LEFT OUTER JOIN CICERON. F_PRETRANSLATED_RESOURCES resources
    ON fact.original_resource_id = resources.id
  LEFT OUTER JOIN CICERON.D_SUBJECTS subjects
    ON fact.subject_id = subjects.id
  LEFT OUTER JOIN CICERON.D_FORMATS formats
    ON fact.format_id = formats.id
  LEFT OUTER JOIN CICERON.D_LANGUAGES lang2
    ON resources.target_language_id = lang2.id
;

CREATE VIEW CICERON.V_PRETRANSLATED_RESOURCES AS
  SELECT
    fact.id,
    fact.project_id,
    fact.target_language_id,
    lang.text target_language,
    fact.theme,
    fact.description,
    fact.tone_id,
    fact.read_permission_level,
    fact.price,
    fact.register_timestamp
  FROM CICERON. F_PRETRANSLATED_RESOURCES fact
  LEFT OUTER JOIN CICERON.D_LANGUAGES lang
    ON fact.target_language_id = lang.id
;

CREATE VIEW CICERON.V_PRETRANSLATED_MY_DOWNLOAD AS
  SELECT
    fact.*,
    users.id user_id
  FROM CICERON. F_PRETRANSLATED_DOWNLOADED_USER fact
  LEFT OUTER JOIN CICERON.D_USERS users
    ON fact.email = users.email
;

CREATE VIEW CICERON.V_PRETRANSLATED_REQUESTER AS
  SELECT
    fact.*,
    users.*
  FROM CICERON.F_PRETRANSLATED_REQUESTER fact
  LEFT OUTER JOIN CICERON.D_USERS users
  ON fact.requester_id = users.id
;

CREATE VIEW CICERON.V_PRETRANSLATED_TRANSLATOR AS
  SELECT
    fact.*,
    users.*
  FROM CICERON.F_PRETRANSLATED_TRANSLATOR fact
  LEFT OUTER JOIN CICERON.D_USERS users
  ON fact.translator_id = users.id
;

CREATE TABLE CICERON.SENTENCES (
    id int NOT NULL,
    original_language_id int4,
    target_language_id int4,
    subject_id int4,
    format_id int4,
    tone_id int4,
    paragraph_id int4,
    sentence_id int4,
    original_sentence varchar(2000),
    translated_sentence varchar(2000),
    PRIMARY KEY (id) 
);
CREATE sequence ciceron.seq_sentences;
GRANT select, update on sequence seq_sentences to ciceron_web;


CREATE TABLE CICERON.D_ADMIN_PAGES (
    id int NOT NULL,
    text varchar(255),
    PRIMARY KEY (id) 
);

CREATE TABLE CICERON.F_AUTHENTICATED_ADMIN_PAGE (
    user_id int NOT NULL,
    page_id int NOT NULL,
    PRIMARY KEY (user_id, page_id) 
);

ALTER TABLE CICERON.F_PRETRANSLATED_RESOURCES
    ADD CONSTRAINT fk_F_PRETRANSLATED_RESOURCES FOREIGN KEY (project_id) REFERENCES F_PRETRANSLATED_PROJECT (id)
    ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE CICERON.F_PRETRANSLATED_TRANSLATOR
    ADD CONSTRAINT fk_F_PRETRANSLATED_TRANSLATOR FOREIGN KEY (translator_id) REFERENCES D_USERS (id)
    ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE CICERON.F_PRETRANSLATED_TRANSLATOR
    ADD CONSTRAINT fk_F_PRETRANSLATED_TRANSLATOR_1 FOREIGN KEY (resource_id) REFERENCES F_PRETRANSLATED_RESOURCES (id)
    ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE CICERON.F_PRETRANSLATED_RESULT_FILE
    ADD CONSTRAINT fk_F_PRETRANSLATED_RESULT_FILE FOREIGN KEY (project_id) REFERENCES F_PRETRANSLATED_PROJECT (id)
    ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE CICERON.F_PRETRANSLATED_RESULT_FILE
    ADD CONSTRAINT fk_F_PRETRANSLATED_RESULT_FILE_1 FOREIGN KEY (resource_id) REFERENCES F_PRETRANSLATED_RESOURCES (id)
    ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE CICERON.F_PRETRANSLATED_DOWNLOADED_USER
    ADD CONSTRAINT fk_F_PRETRANSLATED_DOWNLOADED_USER FOREIGN KEY (resource_id) REFERENCES F_PRETRANSLATED_RESOURCES (id)
    ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE CICERON.F_PRETRANSLATED_REQUESTER
    ADD CONSTRAINT fk_F_PRETRANSLATED_REQUESTER FOREIGN KEY (requester_id) REFERENCES D_USERS (id)
    ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE CICERON.F_AUTHENTICATED_ADMIN_PAGE
    ADD CONSTRAINT fk_F_AUTHENTICATED_ADMIN_PAGE FOREIGN KEY (page_id) REFERENCES CICERON.D_ADMIN_PAGES (id) ON DELETE NO ACTION ON UPDATE NO ACTION;

GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_PROJECT TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_RESOURCES TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_RESULT_FILE TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_DOWNLOADED_USER TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_REQUESTER TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_PRETRANSLATED_TRANSLATOR TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_AUTHENTICATED_ADMIN_PAGE TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. D_ADMIN_PAGES TO ciceron_web;
GRANT SELECT ON TABLE CICERON.V_PRETRANSLATED_PROJECT TO ciceron_web;
GRANT SELECT ON TABLE CICERON.V_PRETRANSLATED_RESOURCES TO ciceron_web;
GRANT SELECT ON TABLE CICERON.V_PRETRANSLATED_MY_DOWNLOAD TO ciceron_web;
GRANT SELECT ON TABLE CICERON.V_PRETRANSLATED_REQUESTER TO ciceron_web;
GRANT SELECT ON TABLE CICERON.V_PRETRANSLATED_TRANSLATOR TO ciceron_web;

GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_PRETRANSLATED_PROJECT TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_PRETRANSLATED_RESOURCES TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_PRETRANSLATED_RESULT_FILE TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_PRETRANSLATED_DOWNLOADED_USER TO ciceron_web;


