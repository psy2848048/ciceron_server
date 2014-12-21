CREATE TABLE Users (
string_id STRING NOT NULL UNIQUE PRIMARY KEY, -- E-mail address 
password_hashed STRING, -- No NOT NULL 'cause of FB, instagram, etc 
nickname STRING NOT NULL, -- This name will be shown in app. 
 
profile_img STRING, 
mother_tongue_language STRING, 
other_language STRING, 
grade INT,
requested_SOS INT,
requested_normal INT,
is_translator BOOL, 
translated_SOS INT,
translated_normal INT,
 
is_FB BOOL, 
is_Instagram BOOL)
; 
 
CREATE TABLE Requests_list (
id INT PRIMARY KEY UNIQUE NOT NULL, 
requester_id STRING NOT NULL,
from_lang STRING NOT NULL, 
to_lang STRING NOT NULL, 
is_SOS BOOL NOT NULL, 
main_text TEXT, 
context_text TEXT, 
image_files STRING, -- separate files with ';' and parse when request 
sound_file STRING, 
request_date TIMESTAMP,
format STRING,
subject STRING,
due_date TIMESTAMP,
translator_id STRING, 
is_request_picked BOOL, 
is_request_finished BOOL,
price FLOAT )
; 
 
CREATE TABLE Result (
request_id INT,
reply_id INT,
is_requester BOOL,
post_time timestamp,
comment_text TEXT, 
is_result BOOL )
;

CREATE TABLE Property (
id STRING,
amount DECIMAL(10,2)
)
;
