CREATE TABLE Users (
string_id STRING NOT NULL UNIQUE PRIMARY KEY, -- E-mail address 
password_hased STRING, -- No NOT NULL 'cause of FB, instagram, etc 
nickname STRING NOT NULL, -- This name will be shown in app. 
 
profile_img STRING, 
mother_tongue_language STRING, 
other_language STRING, 
requested INT, 
is_translator BOOL, 
translated INT,
 
is_FB BOOL, 
is_Instagram BOOL)
; 
 
CREATE TABLE Requests_list (
id INT PRIMARY KEY UNIQUE NOT NULL, 
requestor_id STRING NOT NULL, 
from_lang STRING NOT NULL, 
to_lang STRING NOT NULL, 
is_SOS BOOL NOT NULL, 
main_text TEXT, 
context_text TEXT, 
image_files STRING, -- separate files with ';' and parse when request 
sound_file STRING, 
request_date TIMESTAMP, 
due_date TIMESTAMP,
translator_id STRING, 
translator_pic STRING, 
is_request_picked BOOL, 
is_request_finished BOOL )
; 
 
CREATE TABLE Result (
request_id INT, 
reply_id INT, 
requestor_nick STRING, 
translator_name STRING, 
comment_text TEXT, 
is_result BOOL )
;
