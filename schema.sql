--CREATE DATABASE CICERON;
--USE CICERON;

CREATE TABLE D_USERS (
    id INT,
    email STRING,
    name STRING,
    mother_language_id INT, -- D_LANGUAGES
    is_translator INT,
    other_language_list_id INT,
    profile_pic_path STRING,
    numOfRequestPending INT,
    numOfRequestOngoing INT,
    numOfRequestCompleted INT,
    numOfTranslationPending INT,
    numOfTranslationOngoing INT,
    numOfTranslationCompleted INT,
    badgeList_id INT, -- D_AWARDED_BADGES
    profile_text TEXT
);

CREATE TABLE D_TRANSLATABLE_LANGUAGES (
    id INT,
    user_id INT, -- D_USERS
    language_id INT -- D_LANGUAGES
);

CREATE TABLE D_LANGUAGES (
    id INT,
    text STRING
);

INSERT INTO D_LANGUAGES VALUES (0, 'Korean');
INSERT INTO D_LANGUAGES VALUES (1, 'English(USA)');
INSERT INTO D_LANGUAGES VALUES (2, 'English(UK)');
INSERT INTO D_LANGUAGES VALUES (3, 'Chinese(Mandarin)');
INSERT INTO D_LANGUAGES VALUES (4, 'Chinese(Cantonese)');
INSERT INTO D_LANGUAGES VALUES (5, 'Japanese');
INSERT INTO D_LANGUAGES VALUES (500, 'Others');

CREATE TABLE D_USER_KEYWORDS (
    user_id INT,
    keyword_id INT
);

CREATE TABLE D_KEYWORDS (
    id INT,
    text TEXT
);

CREATE TABLE D_FORMATS (
    id INT,
    text STRING
);

CREATE TABLE D_SUBJECTS(
    id INT,
    text STRING
);

CREATE TABLE D_QUEUE_LISTS (
    id INT,
    request_id INT, -- REQUEST_ID from F_REQUESTS
    user_id INT -- D_USERS
);

CREATE TABLE D_REQUEST_TEXTS (
    id INT,
    path STRING
);

CREATE TABLE D_REQUEST_PHOTOS (
    id INT,
    request_id INT,
    path STRING
);

CREATE TABLE D_REQUEST_FILES (
    id INT,
    path STRING
);

CREATE TABLE D_REQUEST_SOUNDS (
    id INT,
    path STRING
);

CREATE TABLE D_CLIENT_COMPLETED_GROUPS (
    id INT,
user_id INT, -- D_USERS
text STRING
);

CREATE TABLE D_TRANSLATOR_COMPLETED_GROUPS (
    id INT,
    user_id INT, -- D_USERS
    text STRING
);

CREATE TABLE D_CLIENT_COMPLETED_REQUEST_TITLES (
    id INT,
    text STRING
);

CREATE TABLE D_TRANSLATOR_COMPLETED_REQUEST_TITLES (
    id INT,
    text STRING
);

CREATE TABLE D_CONTEXTS (
    id INT,
    text TEXT
);

CREATE TABLE D_COMMENTS (
    id INT,
    text TEXT
);

CREATE TABLE D_TONES (
    id INT,
    text STRING
);

CREATE TABLE D_BADGES (
    id INT,
    text STRING
);

CREATE TABLE D_AWARDED_BADGES (
    id INT,
    user_id INT,  -- badgeList_id from D_USERS
    badge_id INT -- D_BADGES
);

CREATE TABLE D_TRANSLATED_TEXT(
    id INT,
    path STRING
);

CREATE TABLE D_MACHINE_OSS(
    id INT,
    text STRING
);

INSERT INTO D_MACHINE_OSS VALUES (0, 'android_phone');
INSERT INTO D_MACHINE_OSS VALUES (1, 'android_tab');
INSERT INTO D_MACHINE_OSS VALUES (2, 'ios_phone');
INSERT INTO D_MACHINE_OSS VALUES (3, 'ios_tab');

CREATE TABLE D_MACHINES (
    id INT,
    user_id INT,
    os_id INT, -- D_MACHINE_OSS
    reg_key STRING,
    is_push_allowed INT
);

CREATE TABLE F_REQUESTS (
    id INT,
    client_user_id INT, -- D_USERS
    original_lang_id INT, -- D_LANGUAGES
    target_lang_id INT, -- D_LANGUAGES
    isSos BOOL,
    status_id INT, -- 0: pending, 1: ongoing, 2: completed
    format_id INT, -- D_FORMATS
    subject_id INT, -- D_SUBJECTS
    queue_id INT, -- Useless
    ongoing_worker_id INT, -- D_USERS
    is_text BOOL,
    text_id INT, -- D_REQUEST_TEXTS
    is_photo BOOL,
    photo_id INT, -- D_REQUEST_PHOTOS
    is_file BOOL,
    file_id INT, -- D_REQUEST_FILES
    is_sound BOOL,
    sound_id INT, -- D_REQUEST_SOUNDS
    client_completed_group_id INT, -- D_CLIENT_COMPLETED_GROUPS
    translator_completed_group_id INT, -- D_TRANSLATOR_COMPLETED_GROUPS
    client_title_id INT, -- D_CLIENT_COMPLETED_REQUEST_TITLES
    translator_title_id INT, -- D_TRANSLATOR_COMPLETED_REQUEST_TITLES
    is_paid BOOL,
    registered_time TIMESTAMP,
    due_time TIMESTAMP,
    expected_time TIMESTAMP,
    submitted_time TIMESTAMP,
    points DOUBLE,
    context_id INT, -- D_CONTEXTS
    comment_id INT, -- D_COMMENTS
    tone_id INT, -- D_TONES
    translatedText_id INT, -- D_TRANSLATED_TEXT
    feedback_score INT,
    start_translating_time TIMESTAMP
);

CREATE TABLE PASSWORDS (
    user_id INT, -- D_USERS
    hashed_pass STRING
);

CREATE TABLE REVENUE (
id INT, -- D_USER
amount DECIMAL(10,2)
);

CREATE TABLE PAYMENT_INFO (
    id INT,
    request_id INT,
    client_id INT,
    payed_via STRING,
    order_no STRING,
    pay_amount DOUBLE,
    payed_time TIMESTAMP,
    translator_id INT,
    is_payed_back BOOL,
    back_amount DOUBLE,
    back_time TIMESTAMP
);

CREATE VIEW V_REQUESTS as
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
    comments.text comment, --40
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
    F_REQUESTS fact
  LEFT OUTER JOIN D_USERS user_client ON fact.client_user_id = user_client.id
  LEFT OUTER JOIN D_USERS user_translator ON fact.ongoing_worker_id = user_translator.id
  LEFT OUTER JOIN D_LANGUAGES original_lang ON fact.original_lang_id = original_lang.id
  LEFT OUTER JOIN D_LANGUAGES target_lang ON fact.target_lang_id = target_lang.id
  LEFT OUTER JOIN D_FORMATS format ON fact.format_id = format.id
  LEFT OUTER JOIN D_SUBJECTS subject ON fact.subject_id = subject.id
  LEFT OUTER JOIN D_CONTEXTS contexts ON fact.context_id = contexts.id
  LEFT OUTER JOIN D_COMMENTS comments ON fact.comment_id = comments.id
  LEFT OUTER JOIN D_TONES tones ON fact.tone_id = tones.id
  LEFT OUTER JOIN D_CLIENT_COMPLETED_GROUPS client_groups
             ON fact.client_completed_group_id = client_groups.id
  LEFT OUTER JOIN D_TRANSLATOR_COMPLETED_GROUPS translator_groups
             ON fact.translator_completed_group_id = translator_groups.id
  LEFT OUTER JOIN D_CLIENT_COMPLETED_REQUEST_TITLES client_titles
             ON fact.client_title_id = client_titles.id
  LEFT OUTER JOIN D_TRANSLATOR_COMPLETED_REQUEST_TITLES translator_title
             ON fact.translator_title_id = translator_title.id
  LEFT OUTER JOIN D_TRANSLATED_TEXT result
             ON fact.translatedText_id = result.id
            ;

CREATE VIEW V_TRANSLATABLE_LANGUAGES as
  SELECT
    fact.id id,
    fact.user_id user_id,
    users.email user_email,
    users.name user_name,
    fact.language_id translatable_language_id,
    languages.text translatable_language
  FROM
    D_TRANSLATABLE_LANGUAGES fact
  LEFT OUTER JOIN D_USERS users ON fact.user_id = users.id
  LEFT OUTER JOIN D_LANGUAGES languages ON fact.language_id = languages.id;

CREATE VIEW V_QUEUE_LISTS as
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
    D_QUEUE_LISTS fact
  LEFT OUTER JOIN D_USERS users ON fact.user_id = users.id;

CREATE TABLE USER_ACTIONS (
    user_id INT,
    lati DOUBLE,
    longi DOUBLE,
    method STRING,
    api STRING,
    request_id INT,
    log_time TIMESTAMP
);

CREATE TABLE RETURN_MONEY_BANK_ACCOUNT (
    id INT,
    order_no TEXT,
    user_id INT,
    bank_name TEXT,
    account_no INT,
    request_time TIMESTAMP,
    amount DECIMAL(10,2),
    is_returned INT,
    return_time TIMESTAMP
);

CREATE TABLE D_NOTI_TYPE (
    id INT,
    text STRING
);

INSERT INTO D_NOTI_TYPE VALUES (0, 'new_request_alarm');
INSERT INTO D_NOTI_TYPE VALUES (1, 'enter_expected_time');
INSERT INTO D_NOTI_TYPE VALUES (2, 'your_request_is_rated');
INSERT INTO D_NOTI_TYPE VALUES (3, 'deadline_exceeded');
INSERT INTO D_NOTI_TYPE VALUES (4, 'due_time_extended');
INSERT INTO D_NOTI_TYPE VALUES (5, 'cancel_due_to_no_expectedDue');

INSERT INTO D_NOTI_TYPE VALUES (6, 'start_translating');
INSERT INTO D_NOTI_TYPE VALUES (7, 'check_expected_deadline');
INSERT INTO D_NOTI_TYPE VALUES (8, 'give_up_translation');
INSERT INTO D_NOTI_TYPE VALUES (9, 'no_expectedDue_go_to_stoa');
INSERT INTO D_NOTI_TYPE VALUES (10, 'finish_request');
INSERT INTO D_NOTI_TYPE VALUES (11, 'not_finish_request');
INSERT INTO D_NOTI_TYPE VALUES (12, 'no_translator_comes');

INSERT INTO D_NOTI_TYPE VALUES (13, 'youve_got_badge');
INSERT INTO D_NOTI_TYPE VALUES (14, 'paid_back');

CREATE TABLE F_NOTIFICATION (
    user_id INT,
    noti_type_id INT,
    target_user_id INT,
    request_id INT,
    ts TIMESTAMP,
    is_read INT
);

CREATE VIEW V_NOTIFICATION as
  SELECT
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
    fact.ts ts, --16
    fact.is_read is_read --17
  FROM F_NOTIFICATION fact
  LEFT OUTER JOIN D_USERS users ON fact.user_id = users.id
  LEFT OUTER JOIN D_USERS users2 ON fact.target_user_id = users2.id
  LEFT OUTER JOIN D_NOTI_TYPE noti ON fact.noti_type_id = noti.id
  LEFT OUTER JOIN V_REQUESTS req ON fact.request_id = req.request_id;
