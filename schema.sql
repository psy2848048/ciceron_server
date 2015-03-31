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
    machine_id INT, -- D_MACHINES
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

CREATE TABLE D_MACHINE_OSS(
    id INT,
    text STRING
);

CREATE TABLE D_MACHINES (
    id INT,
    os_id INT, -- D_MACHINE_OSS
    reg_key STRING
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
    queue_id INT, -- D_QUEUE_LISTS
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
    registered_time TIMESTAMP,
    due_time TIMESTAMP,
    points DOUBLE,
    context_id INT, -- D_CONTEXTS
    comment_id INT, -- D_COMMENTS
    tone_id INT -- D_TONES
);

CREATE TABLE PASSWORDS (
    user_id INT, -- D_USERS
    hashed_pass STRING
);

CREATE TABLE REVENUE (
id INT, -- D_USER
amount DECIMAL(10,2)
);

CREATE VIEW V_REQUESTS as
  SELECT
    -- Client
    fact.id request_id,
    fact.client_user_id client_user_id,
    user_client.email client_email,
    user_client.name client_name,
    user_client.profile_pic_path client_profile_pic_path,
    -- Translator
    fact.ongoing_worker_id ongoing_worker_id,
    user_translator.email translator_email,
    user_translator.name translator_name,
    user_translator.profile_pic_path translator_profile_pic_path,
    user_translator.numOfTranslationPending numOfTranslationPending,
    user_translator.numOfTranslationOngoing numOfTranslationOngoing,
    user_translator.numOfTranslationCompleted numOfTranslationCompleted,
    user_translator.badgeList_id translator_badgeList_id,
    -- Language
    fact.original_lang_id original_lang_id,
    original_lang.text original_lang,
    fact.target_lang_id target_lang_id,
    target_lang.text target_lang,
    -- Request status
    fact.isSos isSos,
    fact.status_id status_id,
    fact.format_id format_id,
    format.text format,
    fact.subject_id subject_id,
    subject.text subject,
    fact.queue_id queue_id,

    fact.registered_time registered_time,
    fact.due_time due_time,
    fact.points points,
    -- Request type
    fact.is_text is_text,
    fact.text_id text_id,
    fact.is_photo is_photo,
    fact.photo_id photo_id,
    fact.is_file is_file,
    fact.file_id file_id,
    fact.is_sound is_sound,
    fact.sound_id sound_id,
    -- Request more info
    fact.context_id context_id,
    contexts.text context,
    fact.comment_id comment_id,
    comments.text comment,
    fact.tone_id tone_id,
    tones.text tone,
    -- Grouping
    fact.client_completed_group_id client_completed_group_id,
    client_groups.text client_completed_group,
    fact.client_title_id client_title_id,
    client_titles.text client_title,
    fact.translator_completed_group_id translator_completed_group_id,
    translator_groups.text translator_completed_group,
    fact.translator_title_id translator_title_id,
    translator_title.text translator_title

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
             ON fact.translator_title_id = translator_title.id;

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
    users.profile_pic_path profile_pic_path
  FROM
    D_QUEUE_LISTS fact
  LEFT OUTER JOIN D_USERS users ON fact.user_id = users.id;
