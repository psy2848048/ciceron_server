<%@ page contentType="text/html; charset=utf-8"%>
<%@ include file="incMerchant.jsp" %>
<%
	InetAddress inet = InetAddress.getLocalHost();
		
	Timestamp toDay = new Timestamp((new Date()).getTime());
	Timestamp nxDay = getTimestampWithSpan(toDay, 1);
	String VbankExpDate = nxDay.toString();
	VbankExpDate = VbankExpDate.substring(0, 10); 
	VbankExpDate = VbankExpDate.replaceAll("-", "");

	String ediDate = getyyyyMMddHHmmss();
	
	String merchantKey = "J/ca4+s3HD/TasgTVMb3IC6e3rkx7j7C9N5jAbFQ0ecs1Eq3dmvHvrZqQjj7gJk6LJiuXb+4u9Ha5WlreY6U6g==";
	String merchantID = "ciceron00m";
	int price = Integer.parseInt(request.getParameter("price"));
	String md_src = ediDate + merchantID + price + merchantKey;
	DataEncrypt md5_enc =  new DataEncrypt();
	String hash_String  = md5_enc.encrypt(md_src);

    String productName = request.getParameter("productName");
    String invoiceNo = request.getParameter("invoiceNo");
    String clientName = request.getParameter("clientName");
    String clientMail = request.getParameter("clientMail");
    String clientTel = request.getParameter("clientTel");

%>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>씨세론 B2B 결제</title>
<link rel="stylesheet" href="css/basic.css" type="text/css" />
<link rel="stylesheet" href="css/style.css" type="text/css" />

<script src="https://web.nicepay.co.kr/flex/js/nicepay_tr_utf.js" language="javascript"></script>

<script language="javascript">
NicePayUpdate();

function nicepay() {
	var payForm		= document.payForm;
    console.log(payForm);
		
	goPay(payForm);
}

function nicepayClose()
{
	alert("결제에 실패하셨습니다.");
}

function nicepaySubmit(){
    /**
     * Callback API is inserted later
     * */
	
	document.payForm.submit();
}

function chkTransType(value)
{
	document.payForm.TransType.value = value;
}

function chkPayType()
{
	document.payForm.PayMethod.value = checkedButtonValue('selectType');
}
</script>
</head>
<body>
<br>
<br>
<form name="payForm" method="post" action="nicePayResult.jsp">
<table width="632" border="0" cellspacing="0" cellpadding="0" align="center">
  <tr>
  	<td >
  	  <table width="632" border="0" cellspacing="0" cellpadding="0" class="title">
        <tr>
          <td width="35">&nbsp;</td>
          <td>결제 전 정보 확인 페이지</td>
          <td>&nbsp;</td>
        </tr>
      </table>
    </td>
  </tr>
  <tr>
    <td align="left" valign="top" background="images/bodyMiddle.gif">
    <table width="632" border="0" cellspacing="0" cellpadding="0">
      <tr>
        <td width="35" height="10">&nbsp;</td> 
        <td width="562">&nbsp;</td>
        <td width="35">&nbsp;</td>
      </tr>
      <tr>
        <td height="30">&nbsp;</td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="15">&nbsp;</td>
        <td>&nbsp;</td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="30">&nbsp;</td> 
        <td class="bold"><img src="images/bullet.gif" />정보 확인 후 결제를 진행해 주세요.
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td >&nbsp;</td>
        <td ><table width="562" border="0" cellspacing="0" cellpadding="0" class="talbeBorder" >
          <!--
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead01">¿¿ ¿¿</td> 
            <td id="borderBottom" >
              <input type="checkbox" name="selectType" value="CARD" onClick="javascript:chkPayType();">카드
			  <input type="checkbox" name="selectType" value="BANK" onClick="javascript:chkPayType();">이체
			  <input type="checkbox" name="selectType" value="VBANK" onClick="javascript:chkPayType();">가상계좌
			  <input type="checkbox" name="selectType" value="CELLPHONE" onClick="javascript:chkPayType();">휴대폰결제
			</td>
          </tr>
          -->
          <!--
          <tr>
			<td width="100" height="30" id="borderBottom" class="thead02" >결제수단</td>
			<td id="borderBottom" >
			  <input type="radio" name="TransTypeRadio" value="1" onClick="javascript:chkTransType('1')" >에스크로</input>
			</td>
		  </tr>
          -->
	      <input type="hidden" name="TransTypeRadio" value="0" onClick="javascript:chkTransType('0')" />
		  <tr>
            <td width="100" height="30" id="borderBottom" class="thead01">*상품명</td> 
            <td id="borderBottom" ><input name="GoodsName" type="text" value="<%=productName%>" style="background-color:gray" readonly /></td>
          </tr>
          <tr>
              <td width="100" height="30" id="borderBottom" class="thead02">상품가격</td> 
            <td id="borderBottom" ><input name="Amt" type="text" value="<%=price%>" style="background-color:gray" readonly /></td>
          </tr>
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead01">상품주문번호</td> 
            <td id="borderBottom" ><input name="Moid" type="text" value="<%=invoiceNo%>"/ style="background-color:gray" readonly ></td>
          </tr>
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead02">*구매자명</td> 
            <td id="borderBottom" ><input name="BuyerName" type="text" value="<%=clientName%>"/></td>
          </tr> 
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead01">*구매자 이메일</td> 
            <td id="borderBottom" ><input name="BuyerEmail" type="text" value="<%=clientMail%>"/></td>
          </tr>
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead02">* 전화번호</td> 
            <td id="borderBottom" ><input name="BuyerTel" type="text" value="<%=clientTel%>"/></td>
          </tr>

          <!--
          <tr>
            <td width="100" height="30" id="borderBottom" class="thead02"></td> 
            <td id="borderBottom" >
				<select name="SkinType">
					<option value="blue">BLUE</option>
					<option value="purple">PURPLE</option>
					<option value="red">RED</option>
					<option value="green">GREEN</option>
				</select></td>
          </tr>
          -->
         
        </table></td>
        <td height="15">&nbsp;</td>
      </tr>
      <tr>
      	<td height="60"></td>
        <td class="btnCenter"><input type="button" value="결제하기" onClick="javascript:nicepay();"></td> 
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="15"></td>  
        <td >&nbsp;</td>
        <td>&nbsp;</td>
      </tr>
      <tr>
        <td height="10"></td>  
        <td >&nbsp;</td>
        <td>&nbsp;</td>
      </tr>  
    </table></td>
  </tr>
  <tr>
    <td><img src="images/bodyBottom.gif" /></td>
  </tr>
</table>

<!-- Mall Parameters --> 
<input type="hidden" name="MID" value="<%=merchantID%>">
<input type="hidden" name="PayMethod" value="CARD,BANK,VBANK">
<input type="hidden" name="GoodsCnt" value="1">
<input type="hidden" name="BuyerAddr" value="">

<input type="hidden" name="UserIP" value="<%=request.getRemoteAddr()%>">
<input type="hidden" name="MallIP" value="<%=inet.getHostAddress()%>">

<input type="hidden" name="TransType" value="0">

<input type="hidden" name="OptionList" value="">

<input type="hidden" name="VbankExpDate" value="<%=VbankExpDate%>"> 

<input type="hidden" name="MallUserID" value=""> 
<input type="hidden" name="SUB_ID" value="">
<input type="hidden" name="GoodsCl" value="">
<input name="EncodeParameters" type="hidden" value="CardNo,CardExpire,CardPwd"/>
<input type="hidden" name="EdiDate" value="<%=ediDate%>">
<input type="hidden" name="EncryptData" value="<%=hash_String%>" >
<input type="hidden" name="SocketYN" value="Y">
<input type="hidden" name="TrKey" value="">

</form>
</body>
</html>
