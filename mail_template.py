class mail_format:

    translator_new_ticket_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 A new ticket is waiting for your help!<br>
                 Jump into <a href='%(link)s' target='_blank'>here</a> and throw their worriness away!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_new_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_new_ticket_kr
            return self.translator_new_ticket_en
        elif language_id == 1:
            return self.translator_new_ticket_en

    translator_check_expected_time_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Have you ever checked your translation? Is it OK?<br>
                 Then, please inform when you might finish up their woriness via <a href='%(link)s' target='_blank'>here</a>!<br>
                 <br>
                 <span style='color:#DC143C'><h3>ATTENTION!</h3></span><br>
                 <h4>If you don't answer until %(expected)s, other hero might work for this ticket instead of you!</h4>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_check_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_check_expected_time_kr
            return self.translator_check_expected_time_en
        elif language_id == 1:
            return self.translator_check_expected_time_en

    translator_complete_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Thank you for saving a person from worriness!<br>
                 How about moving to your profile and checking the rate and account?<br>
                 <br>
                 Please come again and reduce entropy of the earth!<br>
                 We are looking forward to coming back!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_complete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_complete_kr
            return self.translator_complete_en
        elif language_id == 1:
            return self.translator_complete_en

    translator_exceeded_due_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 We are terribly sorry to inform that you are ceased to access  <a href='%(link)s' target='_blank'>your ticket</a>due to expired deadline.<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_exceeded_due(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_exceeded_due_kr
            return self.translator_exceeded_due_en
        elif language_id == 1:
            return self.translator_exceeded_due_en

    translator_extended_due_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Congrats! Despite that you missed the deadline, the client has just extended <a href='%(link)s' target='_blank'>your ticket</a> until %(new_due).<br>
                 Wish not to miss deadline again :) Peace!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_extended_due(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_extended_due_kr
            return self.translator_extended_due_en
        elif language_id == 1:
            return self.translator_extended_due_en

    translator_no_answer_expected_time_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 We are terribly sorry to inform that other hero will work for <a href='%(link)s' target='_blank'>your ticket</a> due to no response of expected finish.<br>
                 Was it hard? Then, how about visiting to stoa and helping for another tickets?<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def translator_no_answer_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_no_answer_expected_time_kr
            return self.translator_no_answer_expected_time_en
        elif language_id == 1:
            return self.translator_no_answer_expected_time_en

    client_take_ticket_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 <b>%(hero)s</b>&nbsp;is your hero for <a href='%(link)s' target='_blank'>this ticket</a>!<br>
                 How about forget your worriness?
                 Our trusty heroes are working!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_take_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_take_ticket_kr
            return self.client_take_ticket_en
        elif language_id == 1:
            return self.client_take_ticket_en

    client_check_expected_time_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your hero answered the expected finish of ticket!<br>
                 You may check in <a href='%(link)s' target='_blank'>here</a> in detail.<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_check_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_check_expected_time_kr
            return self.client_check_expected_time_en
        elif language_id == 1:
            return self.client_check_expected_time_en

    client_giveup_ticket_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your hero <b>%(hero)s</b>&nbsp;responded that hero cannot help your ticket.<br>
                 You may go to <a href='%(link)s' target='_blank'>your ticket</a> and decide what to do.<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_giveup_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_giveup_ticket_kr
            return self.client_giveup_ticket_en
        elif language_id == 1:
            return self.client_giveup_ticket_en

    client_no_answer_expected_time_go_to_stoa_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your hero has not set his/her expected finish time. Therefore, <a href='%(link)s' target='_blank'>your ticket</a> has just moved to stoa.<br>
                 Your ticket will be served by other heroes.
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_no_answer_expected_time_go_to_stoa(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_answer_expected_time_go_to_stoa_kr
            return self.client_no_answer_expected_time_go_to_stoa_en
        elif language_id == 1:
            return self.client_no_answer_expected_time_go_to_stoa_en

    client_complete_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your ticket has just been solved!<br>
                 Hero %(hero)s submitted a translation <br>
                 <br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> and rate your ticket!<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_complete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_complete_kr
            return self.client_complete_en
        elif language_id == 1:
            return self.client_complete_en

    client_incomplete_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We are sorry to say that your hero miss the deadline of the ticket.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> and make decision of your ticket.<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_incomplete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_incomplete_kr
            return self.client_incomplete_en
        elif language_id == 1:
            return self.client_incomplete_en

    client_no_hero_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We are sorry to say that no hero wants to help your ticket.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> and make decision of your ticket.<br>
                 You may payback, re-post in stoa, and change the reward of the ticket.<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_no_hero(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_hero_kr
            return self.client_no_hero_en
        elif language_id == 1:
            return self.client_no_hero_en

    client_paidback_en="""<img src='%(host)s/api/mail_img/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We are glad to inform that your points have just been paid back to your bank account!<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> to confirm the status. (And your bank account, too!)<br>
                 <br>
                 Best regards,<br>
                 Ciceron team"""

    def client_paid_back(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_hero_kr
            return self.client_paidback_en
        elif language_id == 1:
            return self.client_paidback_en

