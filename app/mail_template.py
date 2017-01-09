# -*- coding: utf-8 -*-

class mail_format:

    translator_new_ticket_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>히어로 %(user)s님,</h1></span><br>
                 <br>
                 새로운 번역 티켓이 등록되었습니다! <a href='%(link)s' target='_blank'>스토아</a>에 한 번 들려 티켓을 확인해 보세요<br>
                 히어로 %(user)s님의 능력을 필요로 하는 티켓들이 스토아에 기다리고 있습니다! 당신의 능력을 보여주세요.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

    translator_new_ticket_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 A new translation ticket has been posted!<br>
                 Please visit the <a href='%(link)s' target='_blank'>STOA</a> to review the request and help someone out with your coveted language skills.<br>
                 <br>
                 Thanks,<br>
                 The CICERON team"""

    def translator_new_ticket(self, language_id):
        if language_id == 0:
            return self.translator_new_ticket_kr
        elif language_id == 1:
            return self.translator_new_ticket_en

    ##################################################################################################################################################

    translator_check_expected_time_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>히어로 %(user)s님,</h1></span><br>
                 <br>
                 오늘도 티켓을 번역해주심에 감사드립니다!<br>
                 지금 이 순간에도 의뢰인께서는 히어로님의 능력을 간절히 기다리고 있습니다.<br>
                 기다리는 고객님을 조금이나마 안심시켜주는 차원에서, 번역 가능한지, 가능하면 언제쯤 완료할 수 있을지 답변 부탁드립니다.<br>
                 잠시만 짬을 내어 의뢰물을 검토해보시고 <a href='%(link)s' target='_blank'>여기</a>에 들러 답해주세요. 잠깐이면 됩니다.<br>
                 <br>
                 <span style='color:#DC143C'><h3>주의!</h3></span><br>
                 <h4>늦어도 %(expected)s까지는 답변을 부탁드립니다. 그 때까지 답변이 없으면 이 티켓은 다른 히어로에게 부탁하게 됩니다. 만약 감당할 수 없을 정도로 어려운 티켓이라면 빨리 말씀해주세요. 빠르면 빠를수록 좋습니다 어렵게 생각하지 않으셔도 됩니다!</h4>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.translator_check_expected_time_kr
        elif language_id == 1:
            return self.translator_check_expected_time_en

    ##################################################################################################################################################

    translator_complete_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear hero %(user)s,</h1></span><br>
                 <br>
                 당신의 능력을 빛내주셔서 감사합니다. 히어로님의 번역 덕분에 의뢰인께서 한시름 덜었을 것이라 믿습니다.<br>
                 프로필 페이지에서 적립금을 확인하실 수 있고, 작업내력 페이지에서 피드백을 확인할 수 있습니다.<br>
                 <br>
                 지금 이 순간에도 당신의 능력을 필요로하는 티켓들이 스토아에서 가디라고 있습니다.<br>
                 히어로님의 능력을 기다립니다.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.translator_complete_kr
        elif language_id == 1:
            return self.translator_complete_en

    ##################################################################################################################################################

    translator_exceeded_due_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>히어로 %(user)s님,</h1></span><br>
                 <br>
                 히어로님께서 번역을 맡은 <a href='%(link)s' target='_blank'>이 티켓</a>이 의뢰인께서 설정한 마감 시간을 넘겼습니다.<br>
                 혹시 마감 시한이 넘지 않았는데 이 메일을 받아보시게 된다면 저희이게 <a href='mailto:webmaster@ciceron.me?Subject=False%20alarm%20report' target='_blank'>연락</a> 부탁드리겠습니다.<br>
                 <br>
                 씨세론 팀""".encode('utf-8')

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
            return self.translator_exceeded_due_kr
        elif language_id == 1:
            return self.translator_exceeded_due_en

    ##################################################################################################################################################

    translator_extended_due_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>히어로 %(user)s님,</h1></span><br>
                 <br>
                 <a href='%(link)s' target='_blank'>이 티켓</a>의 마감시한은 넘겼지만, 의뢰인께서 기한을 %(new_due)s까지 연장해주셨습니다.<br>
                 혹시 새로운 마감 기한에 대하여 의문점이 있으면 언제든지 저희에게 <a href='mailto:webmaster@ciceron.me?Subject=False%20alarm%20report' target='_blank'>연락</a> 부탁드립니다.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.translator_extended_due_kr
        elif language_id == 1:
            return self.translator_extended_due_en

    ##################################################################################################################################################

    translator_no_answer_expected_time_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>히어로 %(user)s님,</h1></span><br>
                 <br>
                 예상 마감시한을 답변해주지 않으셔서 <a href='%(link)s' target='_blank'>이 티켓</a>은 다른 히어로에게 기회가 가게 되었습니다.<br>
                 하지만 낙심하지 않으셔도 됩니다. <a href='%(link)s' target='_blank'>스토아</a>에 가 보시면 더 많은 티켓들이 히어로님의 능력을 기다리고 있습니다!<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.translator_no_answer_expected_time_kr
        elif language_id == 1:
            return self.translator_no_answer_expected_time_en

    ##################################################################################################################################################

    client_take_ticket_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 히어로 <b>%(hero)s</b>&nbsp;님께서 <a href='%(link)s' target='_blank'>이 티켓</a>을 번역해주시기로 했습니다!<br>
                 여러분들의 만족을 위하여 히어로들은 하나하나 꼼곰하게 검토하여 선발했습니다. 저희 히어로들은 단지 한 언어를 다른 언어로 옮겨주는 차원을 넘어, 내용을 읽고 문맥을 파악하여 해당 언어에 가장 알맞은 표현을 찾아낼 줄 아는 사람들입니다.<br>
                 저희 히어로를 믿고 기다려 주세요!<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.client_take_ticket_kr
        elif language_id == 1:
            return self.client_take_ticket_en

    ##################################################################################################################################################

    client_check_expected_time_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 히어로님께서 예상 완료 시간을 답해주셨습니다!<br>
                 자세한 정보는 <a href='%(link)s' target='_blank'>이곳</a>에서 확인해보실 수 있습니다.<br>
                 <b>참고:/b> 예상 완료시간은 어디까지나 <b>참고용</b>입니다. 시스템은 의뢰인님께서 설정해주신 <b>마감 시간</b>을 기준으로 작동합니다.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

    client_check_expected_time_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Your Hero has just updated the expected completion date for your ticket!<br>
                 You may visit <a href='%(link)s' target='_blank'>here</a> for more information.<br>
                 <b>Attention:</b> The 'expected compltetion date' is just only for a <b>reference</b>. CICERON system works <b>based on the deadline you set</b>.
                 <br>
                 Best regards,<br>
                 The CICERON team"""

    def client_check_expected_time(self, language_id):
        if language_id == 0:
            return self.client_check_expected_time_kr
        elif language_id == 1:
            return self.client_check_expected_time_en

    ##################################################################################################################################################

    client_giveup_ticket_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 히어로 <b>%(hero)s</b>님께서 의뢰인님의 티켓은 기한 내에 번역이 어려울거라 답해주셨습니다.<br>
                 <a href='%(link)s' target='_blank'>여기</a>에 가셔서 티켓을 다른 히어로에게 부탁할 지, 아니면 의뢰를 중단할 지 결정해주시기 바랍니다.<br>
                 완벽한 번역만을 제공하겠다는 저희 히어로들의 마음 때문에, 히어로 자신이 감당하지 못하는 수준의 티켓에 대해서는 이렇게 번역불가 의사를 표할 수도 있습니다. 양해 부탁드립니다.<br>
                 이유는 여러가지일 수 있습니다. 시간이 부족하다고 느꼈을수도, 혹은 자신에게 더 맞는 의뢰를 찾았을수도 있습니다.<br>
                 이유불문, 불편을 끼쳐드려 죄송합니다. 문의 사항 있으면 주저하지 말고 저희에게 연락 부탁드립니다!<br>
                 <br>
                 씨세론 팀""".encode('utf-8')

    client_giveup_ticket_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 Oops...<br>
                 Your Hero <b>%(hero)s</b>&nbsp;regretfully responded that your ticket cannot be completed.<br>
                 You may unfold <a href='%(link)s' target='_blank'>your ticket</a> and decide what to do. You may assign to another qualified Hero or opt out of the request.<br>
                 Please bear in mind that our Heros sometimes decide to let go of a ticket, because they are committed to producing only the finest translation works. They may feel that there isn't enough time or that another Hero might be more appropriate for a certain project.<br>
                 In any case, we're so sorry for the hassle. Please let us know if you have any questions!<br>
                 <br>
                 Regretfully,<br>
                 The CICERON team"""

    def client_giveup_ticket(self, language_id):
        if language_id == 0:
            return self.client_giveup_ticket_kr
        elif language_id == 1:
            return self.client_giveup_ticket_en

    ##################################################################################################################################################

    client_no_answer_expected_time_go_to_stoa_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 저희 시스템은 각 티켓의 마감 시한을 감지하여 티켓의 상태를 수정합니다. 그 중 하나로, 티켓 번역 의사를 표해주신 시점부터 마감 시한까지의 1/3이 되는 지점에 다다랐음에도 번역 완료 예상 시간을 답해주지 않으면 티켓을 스토아에 다시 공개하여 다른 히어로에게 기회를 주고 있습니다.<br>
                 안타깝게도, <a href='%(link)s' target='_blank'>당신의 티켓</a>도 이 사유에 따라 스토아에 다시 공개되었습니다.<br>
                 그래도 걱정하진 마세요. 이 티켓에 더욱 적합한 히어로가 다시 의뢰인님을 찾아올 것입니다.<br>
                 문의 사항 있으시면 주저하지 말고 저희에게 연락 부탁드립니다!<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.client_no_answer_expected_time_go_to_stoa_kr
        elif language_id == 1:
            return self.client_no_answer_expected_time_go_to_stoa_en

    ##################################################################################################################################################

    client_complete_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 오래 기다리셨습니다!<br>
                 히어로 %(hero)s님께서 방금 번역을 완료하셨습니다!<br>
                 <br>
                 <a href='%(link)s' target='_blank'>이곳</a>에서 결과물을 확인하시고 평가를 할 수 있습니다. <br>
                 혹시 티켓 의뢰의 전 과정에서 불편한 점이 있으셨으면 주저하지 말고 저희에게 연락 부탁드립니다.<br>
                 <br>
                 Thanks,<br>
                 The CICERON team""".encode('utf-8')

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
            return self.client_complete_kr
        elif language_id == 1:
            return self.client_complete_en

    ##################################################################################################################################################

    client_incomplete_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님께,</h1></span><br>
                 <br>
                 티켓을 번역해주시기로 한 히어로님께서 안타깝게도 기한 내에 결과물을 제출하지 못했다는 소식을 전해드려게 되었습니다.<br>
                 부디 <a href='%(link)s' target='_blank'>이곳에</a> 잠시 방문하시어 기한을 연장할 지, 혹은 티켓을 취소할 지 결정해주시기 바랍니다.<br>
                 대부분의 티켓은 기한 내에 처리가 됩니다. 다만, 어떻게든 자연스럽게 문장을 만들기 위하여 정성을 기울이느라 시간이 늦어질 수는 있습니다.<br>
                 다시 한 번 죄송하다는 말씀 드립니다. 다음 의뢰시에는 좋은 기억을 가져다 드릴 수 있도록 노력하겠습니다!
                 <br>
                 씨세론 팀""".encode('utf-8')

    client_incomplete_en="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>Dear %(user)s,</h1></span><br>
                 <br>
                 We are really sorry to let you know that your Hero has missed the deadline for your ticket.<br>
                 Please visit <a href='%(link)s' target='_blank'>here</a> to either extend the deadline for your Hero or cancel the request entirely.<br>
                 Please bear in mind that your Hero has likely completed most of the work. Sometimes a little more time is all that is needed to churn out the most appropriate, contextually-fitting translation.<br>
                 Once again, we're so sorry for the hassle. We'll do our best to improve your experience.<br>
                 <br>
                 Regretfully,<br>
                 The CICERON team"""

    def client_incomplete(self, language_id):
        if language_id == 0:
            return self.client_incomplete_kr
        elif language_id == 1:
            return self.client_incomplete_en

    ##################################################################################################################################################

    client_no_hero_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 어느 히어로도 당신의 티켓을 선택해주지 않으셨습니다.<br>
                 잠시 시간을 내어 <a href='%(link)s' target='_blank'>이곳</a>을 방문해 주셔서 취소 및 연장 여부를 결정해주시기 바랍니다.<br>
                 <br>
                 저희 히어로들은 문장 호응에 맞는 매끄러운 번역을 위하여 많은 노력과 시간이 들어가기 때문에, 모든 히어로가 번역중이라면 이후 올라오는 티켓은 미처 발견하지 못할 수 있습니다.<br>
                 작은 의문이라도 저희에게 주저하지 말고 문의 부탁드립니다. 항상 발전하는 모습 보여드리려 노력하겠습니다.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.client_no_hero_kr
        elif language_id == 1:
            return self.client_no_hero_en

    ##################################################################################################################################################

    client_paidback_kr="""<img src='%(host)s/api/access_file/img/logo.png'><br>
                 <span style='color:#5F9EA0'><h1>%(user)s님,</h1></span><br>
                 <br>
                 신청하신 포인트 환급이 완료되었습니다.<br>
                 <a href='%(link)s' target='_blank'>이곳</a>에 방문하시어 포인트 환급 상태를 확인해주시기 바랍니다. (그리고 당신의 은행 계좌도요!)<br>
                 문의사항 있으시면 주저말고 연락 부탁드립니다.<br>
                 <br>
                 감사합니다,<br>
                 씨세론 팀""".encode('utf-8')

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
            return self.client_paidback_kr
        elif language_id == 1:
            return self.client_paidback_en

