CREATE TABLE D_USERS (
    id INT,
    email STRING,
    name STRING,
    mother_language_id INT, -- D_LANGUAGES
    is_translator BOOL,
    other_language_list_id INT,
    profile_pic_path STRING
    numOfRequestPending INT,
    numOfRequestOngoing INT,
    numOfRequestCompleted INT,
    numOfTranslationPending INT,
    numOfTranslationOngoing INT,
    numOfTranslationCompleted INT,
    badgeList_id INT, -- D_AWARDED_BADGES
    machine_id INT, -- D_MACHINES
);

CREATE TABLE D_TRANSLATABLE_LANGUAGES (
    id INT,
    user_id INT -- D_USERS
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
    id INT, -- REQUEST_ID from F_REQUESTS
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
    id INT, -- badgeList_id from F_PROFILES
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
    request_id INT,
    client_userid INT, -- D_USERS
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

CREATE TABLE Revenue (
id STRING,
amount DECIMAL(10,2)
);

