--DROP SCHEMA CICERON cascade;
CREATE SCHEMA CICERON;
SET SCHEMA 'CICERON';

CREATE TABLE CICERON.D_USERS (
    id INT not null,
    email varchar(100) not null,
    name varchar(100) not null,
    mother_language_id INT not null, -- D_LANGUAGES
    is_translator BOOLEAN,
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
    
    PRIMARY KEY (id)
);

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
    
    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_LANGUAGES;

INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Korean');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'English(USA)');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'English(UK)');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Chinese(Mandarin)');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Chinese(Cantonese)');
INSERT INTO CICERON.D_LANGUAGES VALUES (nextval('CICERON.SEQ_D_LANGUAGES'), 'Thai');

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

INSERT INTO CICERON.D_NATIONS VALUES (0, 'Korea');
INSERT INTO CICERON.D_NATIONS VALUES (1, 'USA');
INSERT INTO CICERON.D_NATIONS VALUES (2, 'UK');
INSERT INTO CICERON.D_NATIONS VALUES (3, 'China(Mainland)');
INSERT INTO CICERON.D_NATIONS VALUES (4, 'China(Hong Kong, Macao)');
INSERT INTO CICERON.D_NATIONS VALUES (5, 'Thailand');

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
    
    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_F_REQUESTS;

CREATE TABLE CICERON.D_REQUEST_TEXTS (
    id INT,
    path varchar(200),
    text TEXT,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_TEXTS;

CREATE TABLE CICERON.D_REQUEST_PHOTOS (
    id INT,
    path varchar(300),
    bin BYTEA,

    PRIMARY KEY(id)
);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_PHOTOS;

CREATE TABLE CICERON.D_REQUEST_FILES (
    id INT,
    path varchar(300),
    bin BYTEA,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_FILES;

CREATE TABLE CICERON.D_REQUEST_SOUNDS (
    id INT,
    path varchar(300),
    bin BYTEA,

    PRIMARY KEY (id)
);

CREATE SEQUENCE CICERON.SEQ_D_REQUEST_SOUNDS;

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
    PRIMARY KEY (id, request_id, user_id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS
);

CREATE SEQUENCE CICERON.SEQ_D_QUEUE_LISTS;

CREATE TABLE CICERON.D_TRANSLATED_TEXT(
    id INT,
    path varchar(300),
    text TEXT,

    PRIMARY KEY (id)
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
    id INT, -- D_USER
    amount REAL,

    PRIMARY KEY (id),
    FOREIGN KEY (id) REFERENCES CICERON.D_USERS (id)
);

CREATE TABLE CICERON.PAYMENT_INFO (
    id INT,
    request_id INT,
    client_id INT,
    payed_via varchar(20),
    order_no varchar(100),
    pay_amount DECIMAL(10,2),
    payed_time TIMESTAMPTZ,
    translator_id INT,
    is_payed_back BOOLEAN,
    back_amount DECIMAL(10,2),
    back_time TIMESTAMPTZ,
    
    PRIMARY KEY (id),
    FOREIGN KEY (request_id) REFERENCES CICERON.F_REQUESTS (id),
    FOREIGN KEY (client_id) REFERENCES CICERON.D_USERS (id),
    FOREIGN KEY (translator_id) REFERENCES CICERON.D_USERS (id)
);

CREATE SEQUENCE CICERON.SEQ_PAYMENT_INFO;

CREATE VIEW CICERON.V_REQUESTS as
  SELECT
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

    fact.start_translating_time start_translating_time --55

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
    users.profile_text profile_text
  FROM
    CICERON.D_QUEUE_LISTS fact
  LEFT OUTER JOIN CICERON.D_USERS users ON fact.user_id = users.id;

CREATE TABLE CICERON.USER_ACTIONS (
    user_id INT,
    lati REAL,
    longi REAL,
    method varchar(10),
    api varchar(300),
    request_id INT,
    log_time TIMESTAMPTZ
);

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
    req.status_id status_id
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
