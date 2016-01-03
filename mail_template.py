class mail_format:

    translator_new_ticket_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 A new translation ticket has been posted!<br>
                 Please visit the <a href='%(link)s' target='_blank'>STOA</a> to review the request and help someone out with your coveted language skills.<br>
                 <br>
                 Thans,<br>
                 The CICERON team"""

    def translator_new_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_new_ticket_kr
            return self.translator_new_ticket_en
        elif language_id == 1:
            return self.translator_new_ticket_en

    ##################################################################################################################################################

    translator_check_expected_time_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Thank you so much for agreeing to help someone out with your language assets.<br>
                 Just to keep your client rest assured, please let us know when you expect to finish the translation by simply visiting <a href='%(link)s' target='_blank'>here</a>!<br>
                 <br>
                 <span style='color:#DC143C'><h3>ATTENTION!</h3></span><br>
                 <h4>But, if we don't hear from you by %(expected)s, we may have to transfer the ticket to another appropriate Hero. No pressure, though. If you don't think you can finish the job, the sooner we know, the better! It's all for the best. No hard feelings, we promise.</h4>
                 <br>
                 Thanks,<br>
                 The CICERON team"""

    def translator_check_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_check_expected_time_kr
            return self.translator_check_expected_time_en
        elif language_id == 1:
            return self.translator_check_expected_time_en

    ##################################################################################################################################################

    translator_complete_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Thank you for saving someone - both figuratively and literally - with the translation.<br>
                 You're now able to review the client rating and final payment on your profile page.<br>
                 <br>
                 We hope to continue working with you to build the world where nothing gets lost in translation.<br>
                 See you again soon!<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def translator_complete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_complete_kr
            return self.translator_complete_en
        elif language_id == 1:
            return self.translator_complete_en

    ##################################################################################################################################################

    translator_exceeded_due_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 We are terribly sorry to let you know that the access to <a href='%(link)s' target='_blank'>your ticket</a>your ticket</a> has been expired because the deadline has been passed.<br>
                 Please reach out to us if you think there has been an error.<br>
                 <br>
                 Regretfully,<br>
                 The CICERON team"""

    def translator_exceeded_due(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_exceeded_due_kr
            return self.translator_exceeded_due_en
        elif language_id == 1:
            return self.translator_exceeded_due_en

    ##################################################################################################################################################

    translator_extended_due_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 Good news! Even though you missed the deadline, the client has just extended <a href='%(link)s' target='_blank'>your ticket</a> until %(new_due).<br>
                 Please reach out to us if you have any problems meeting the new deadline.<br>
                 <br>
                 Good luck,<br>
                 The CICERON team"""

    def translator_extended_due(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_extended_due_kr
            return self.translator_extended_due_en
        elif language_id == 1:
            return self.translator_extended_due_en

    ##################################################################################################################################################

    translator_no_answer_expected_time_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 We regret to inform you that another Hero will work on <a href='%(link)s' target='_blank'>your last ticket</a> because you haven't tipped us on the expected completion date.<br>
                 Even though this ticket has passed, there are more on our <a href='%(link)s' target='_blank'>STOA</a>. Let's help more people out!<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def translator_no_answer_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return translator_no_answer_expected_time_kr
            return self.translator_no_answer_expected_time_en
        elif language_id == 1:
            return self.translator_no_answer_expected_time_en

    ##################################################################################################################################################

    client_take_ticket_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 <b>Good news!</b> <b>%(hero)s</b>&nbsp;has been assigned as the Hero for <a href='%(link)s' target='_blank'>your ticket</a>!<br>
                 We have meticulously hand-picked qualified Heroes to help out with your translation needs. They not only know how to covert one language to another, but also understand the underlying context of each content.<br>
                 So, rest assured, and wait for your Hero to complete the job!<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def client_take_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_take_ticket_kr
            return self.client_take_ticket_en
        elif language_id == 1:
            return self.client_take_ticket_en

    ##################################################################################################################################################

    client_check_expected_time_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your Hero has just updated the expected completion date for your ticket!<br>
                 You may visit <a href='%(link)s' target='_blank'>here</a> for more information.<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def client_check_expected_time(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_check_expected_time_kr
            return self.client_check_expected_time_en
        elif language_id == 1:
            return self.client_check_expected_time_en

    ##################################################################################################################################################

    client_giveup_ticket_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Oops...<br>
                 Your Hero <b>%(hero)s</b>&nbsp;regretfully responded that your ticket cannot be completed.<br>
                 You may unfold <a href='%(link)s' target='_blank'>your ticket</a> and decide what to do. You may assign to another qualified Hero or opt out of the request.<br>
                 Please bear in mind that our Heros sometimes decide to let go of a ticket, because they are committed to producing only the finest translation works. They may feel that there isn't enough time or that another Hero might be more appropriate for a certain project.<br>∫ any case, we're so sorry for the hassle. Please let us know if you have any questions!<br>
                 <br>
                 Regretfully,<br>
                 The CICERON team"""

    def client_giveup_ticket(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_giveup_ticket_kr
            return self.client_giveup_ticket_en
        elif language_id == 1:
            return self.client_giveup_ticket_en

    ##################################################################################################################################################

    client_no_answer_expected_time_go_to_stoa_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 As you may know, we routinely check to ensure expedited completion of all tickets. We normally do this by the 1/3 point of your designated deadline.<br>
                 Unfortunately, however, your Hero has opted not to tip us on the expected completion date this time. So, we have decided to transfer <a href='%(link)s' target='_blank'>your ticket</a> back to the STOA.<br>
                 Don't worry though! Your ticket will be assigned to another, possible more capable, Hero.<br>
                 Please reach out to us if you have any questions!<br>
                 <br>
                 Always at your service,<br>
                 The CICERON team"""

    def client_no_answer_expected_time_go_to_stoa(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_answer_expected_time_go_to_stoa_kr
            return self.client_no_answer_expected_time_go_to_stoa_en
        elif language_id == 1:
            return self.client_no_answer_expected_time_go_to_stoa_en

    ##################################################################################################################################################

    client_complete_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Awesome news!<br>
                 Your Hero %(hero)s has just submitted the translation. Your ticket is now completed.<br>
                 <br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> and rate your Hero. We're open to hearing anything you have to say about the experience.<br>
                 <br>
                 Thanks,<br>
                 The CICERON team"""

    def client_complete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_complete_kr
            return self.client_complete_en
        elif language_id == 1:
            return self.client_complete_en

    ##################################################################################################################################################

    client_incomplete_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We are really sorry to let you know that your Hero has missed the deadline for your ticket.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> to either extend the deadline for your Hero or cancel the request entirely.<br>
                 Please bear in mind that your Hero has likely completed most of the work. Sometimes a little more time is all that is needed to churn out the most appropriate, contextually-fitting translation.<br>nce again, we're so sorry for the hassle. We'll do our best to improve your experience.<br>
                 <br>
                 Regretfully,<br>
                 The CICERON team"""

    def client_incomplete(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_incomplete_kr
            return self.client_incomplete_en
        elif language_id == 1:
            return self.client_incomplete_en

    ##################################################################################################################################################

    client_no_hero_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Oh oh...<br>
                 We've waited, pinged, and shook things up a little more. But, no Hero has decided to pick up your ticket.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> and decide what to do about your ticket.<br>
                 You may opt out, repost in the STOA, or change the price of your ticket.<br>
                 <br>
                 Please understand that our Heroes are committed to producing only the most appropriate, contextually-correct translations. They may sometimes decide not to pick up a ticket, because they feel that such a commitment cannot be met under certain conditions. It's all for the best, we promise.<br>
                 In any case, please reach out to us if you have any questions about the process. We'll be more than glad to help enhance your experience!<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def client_no_hero(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_hero_kr
            return self.client_no_hero_en
        elif language_id == 1:
            return self.client_no_hero_en

    ##################################################################################################################################################

    client_paidback_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We're glad to inform you that your points have been restored back to your account.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> to review the account status.<br>
                 Let us know if you have any questions!<br>
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def client_paid_back(self, language_id):
        if language_id == 0:
            # Later, should be Korean
            # return client_no_hero_kr
            return self.client_paidback_en
        elif language_id == 1:
            return self.client_paidback_en

