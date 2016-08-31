﻿GRANT USAGE ON SCHEMA CICERON TO ciceron_web;

GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_awarded_badges TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_badges TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_client_completed_groups TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_client_completed_request_titles TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_comments TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_contexts TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_facebook_users TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_formats TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_keywords TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_languages TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_machine_oss TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_machines TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_noti_type TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_queue_lists TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_request_files TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_request_photos TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_request_sounds TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_request_texts TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_subjects TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_tones TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_translatable_languages TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_translated_text TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_translator_completed_groups TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_translator_completed_request_titles TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_d_users TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_f_requests TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_payment_info TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_promotioncodes_common TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_promotioncodes_user TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_return_money_bank_account TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_usedpromotion_common TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.seq_f_notification TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_USER_ACTIONS TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_BLACKLIST TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_D_I18N_VARIABLE_NAMES TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_D_I18N_TEXTS TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_I18N_TEXT_MAPPINGS TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_I18N_VALUES TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_GROUP_REQUESTS_USERS TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_D_TRANSLATED_FILES TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_D_UNORGANIZED_TRANSLATED_RESULT TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_READ_PUBLIC_REQUESTS_USERS TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_F_PUBLIC_REQUESTS_COPYRIGHT_CHECK TO ciceron_web;
GRANT SELECT, UPDATE ON SEQUENCE CICERON.SEQ_INIT_TRANSLATION_TEMP TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_awarded_badges TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_badges TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_client_completed_groups TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_client_completed_request_titles TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_comments TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_contexts TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_facebook_users TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_formats TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_keywords TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_languages TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_machine_oss TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_machines TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_nations TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_noti_type TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_queue_lists TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_request_files TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_request_photos TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_request_sounds TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_request_texts TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_residence TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_subjects TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_tones TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_translatable_languages TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_translated_text TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_translator_completed_groups TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_translator_completed_request_titles TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_user_keywords TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. d_users TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. emergency_code TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. f_notification TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. f_requests TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. passwords TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. payment_info TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. promotioncodes_common TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. promotioncodes_user TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. return_money_bank_account TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. revenue TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. usedpromotion_common TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. user_actions TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. v_notification TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. v_queue_lists TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. v_requests TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. v_translatable_languages TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON. F_USER_PROFILE_PIC TO ciceron_web;
GRANT SELECT, UPDATE, INSERT ON TABLE CICERON.COMMENT_SENTENCE TO ciceron_web;
GRANT SELECT, UPDATE, INSERT ON TABLE CICERON.COMMENT_PARAGRAPH TO ciceron_web;
GRANT SELECT, UPDATE, INSERT ON TABLE CICERON.return_point TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.D_I18N_VARIABLE_NAMES TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.D_I18N_TEXTS TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.F_I18N_TEXT_MAPPINGS TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.F_I18N_VALUES TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.F_GROUP_REQUESTS_USERS TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.D_TRANSLATED_FILES TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.D_UNORGANIZED_TRANSLATED_RESULT TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.F_READ_PUBLIC_REQUESTS_USERS TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.F_PUBLIC_REQUESTS_COPYRIGHT_CHECK TO ciceron_web;
GRANT SELECT, UPDATE, INSERT, DELETE ON TABLE CICERON.INIT_TRANSLATION_TEMP TO ciceron_web;
