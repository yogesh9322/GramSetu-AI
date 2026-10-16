import os
import glob
import time
import re
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()

_LLM = None
_SCHEME_CACHE = None

def detect_language(text):
    marathi_words = ["काय","कसे","मला","आहे","करा","सांगा","मी","माझे","कुठे","योजनेसाठी","पात्र","द्या","आहेत","करायचे","नाही","त्यांना","कशी","कोण","मिळते","भरावा","लागतो","आपल्या","होते","झाले","करतो"]
    hindi_words = ["क्या","कैसे","मुझे","है","करो","बताओ","मैं","मेरा","कहाँ","होता","करना","मिलता","जाना","लेना","देना","चाहिए","हैं","उनका","उनके","इसके","उसके"]
    mc = sum(1 for w in marathi_words if w in text)
    hc = sum(1 for w in hindi_words if w in text)
    if mc > hc: return "marathi"
    elif hc > 0: return "hindi"
    return "english"

def get_prompt(language):
    if language == "marathi":
        template = """तुम्ही एक मदतगार AI सहाय्यक आहात जे महाराष्ट्रातील ग्रामीण लोकांना सरकारी योजनांबद्दल मदत करतात.
खालील माहितीच्या (Context) आणि अधिकृत सरकारी योजनांच्या माहितीच्या आधारे विचारलेल्या प्रश्नाचे संपूर्ण, सविस्तर आणि अचूक उत्तर सोप्या मराठीत (देवनागरी लिपीत) द्या.
खालील मुद्द्यांचा स्पष्ट समावेश करा:
1. योजनेचे मुख्य फायदे (Key Benefits)
2. कोण पात्र आहे (Eligibility)
3. आवश्यक कागदपत्रे (Required Documents)
4. अर्ज कसा करावा - सविस्तर पायरी पायरीने मार्गदर्शन (How to Apply)
5. हेल्पलाइन नंबर आणि अधिकृत पोर्टल (Helpline & Official Website)

Context: {context}
प्रश्न: {question}
उत्तर (मराठीत):"""
    elif language == "hindi":
        template = """आप एक मददगार AI सहायक हैं जो भारत के ग्रामीण नागरिकों को सरकारी योजनाओं की पूरी जानकारी देते हैं।
नीचे दी गई जानकारी (Context) और आधिकारिक सरकारी नियमों के आधार पर प्रश्न का संपूर्ण, विस्तृत और स्पष्ट उत्तर हिंदी (देवनागरी लिपि) में दें।
उत्तर में निम्नलिखित सभी बिंदुओं को स्पष्ट रूप से शामिल करें:
1. योजना के मुख्य लाभ (Key Benefits)
2. पात्रता - कौन आवेदन कर सकता है (Eligibility)
3. आवश्यक दस्तावेज़ (Required Documents)
4. आवेदन कैसे करें - चरण-दर-चरण प्रक्रिया (How to Apply)
5. हेल्पलाइन नंबर और आधिकारिक पोर्टल (Helpline & Official Website)

Context: {context}
प्रश्न: {question}
उत्तर (हिंदी में):"""
    else:
        template = """You are a helpful AI assistant supporting rural Indian citizens with government schemes.
Provide a complete, comprehensive, and detailed answer in clear English based on the provided context and official government scheme details.
Include all key details:
1. Main Benefits
2. Eligibility Criteria
3. Required Documents
4. Step-by-Step Application Process
5. Helpline Number & Official Website

Context: {context}
Question: {question}
Answer (in English):"""
    return PromptTemplate(template=template, input_variables=["context", "question"])

def get_all_schemes():
    """Load and cache all 60+ government scheme text files (Total ~35KB, instant 0ms)"""
    global _SCHEME_CACHE
    if _SCHEME_CACHE is None:
        data_dir = os.path.join(os.path.dirname(__file__), "../data")
        files = glob.glob(os.path.join(data_dir, "*.txt"))
        schemes = []
        for fp in files:
            fname = os.path.basename(fp).replace(".txt", "")
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    content = f.read()
                schemes.append({
                    "id": fname,
                    "title": fname.replace("_", " "),
                    "content": content
                })
            except Exception:
                pass
        _SCHEME_CACHE = schemes
        print(f"[INFO] Cached {len(_SCHEME_CACHE)} schemes into memory ({sum(len(s['content']) for s in _SCHEME_CACHE)} bytes)")
    return _SCHEME_CACHE

SCHEME_KEYWORDS = {
    "pm_kisan": ["pm kisan", "kisan samman", "पीएम किसान", "किसान सम्मान निधि", "६०००", "6000", "शेतकरी अनुदान", "किसान सम्मान"],
    "fasal_bima": ["fasal bima", "pmfby", "crop insurance", "फसल बीमा", "पीक विमा", "फसल नुकसान", "खरीफ", "रबी", "फसल", "बीमा"],
    "pm_fasal_bima_rabi": ["fasal bima rabi", "रबी फसल बीमा", "रब्बी पीक विमा"],
    "kisan_credit_card": ["kisan credit card", "kcc", "किसान क्रेडिट कार्ड", "केसीसी", "पीक कर्ज", "किसान लोन"],
    "ayushman": ["ayushman", "pmjay", "golden card", "health card", "आयुष्मान भारत", "आयुष्मान कार्ड", "५ लाख", "5 lakh", "आरोग्य कार्ड", "आयुष्मान"],
    "awas_yojana": ["pm awas", "pmay", "housing", "आवास योजना", "घरकुल", "घरकुल योजना", "पक्के मकान", "आवास"],
    "mgnrega": ["mgnrega", "nrega", "job card", "मनरेगा", "जॉब कार्ड", "रोजगार हमी", "१०० दिवस", "100 days", "रोजगार कार्ड"],
    "pm_ujjwala": ["ujjwala", "lpg", "gas", "cylinder", "उज्ज्वला", "गैस कनेक्शन", "सिलेंडर", "मोफत गॅस", "उज्वला"],
    "sukanya_samriddhi": ["sukanya", "samriddhi", "girl child", "सुकन्या समृद्धि", "मुलगी योजना", "बेटी", "सुकन्या"],
    "e_shram": ["e shram", "eshram", "shramik", "ई श्रम", "श्रम कार्ड", "मजदूर कार्ड", "ई-श्रम", "कामगार कार्ड"],
    "pm_mudra": ["mudra", "business loan", "मुद्रा योजना", "शिशु लोन", "किशोर लोन", "तरुण लोन", "व्यवसाय कर्ज", "मुद्रा"],
    "atal_pension": ["atal pension", "apy", "अटल पेंशन", "पेन्शन योजना", "अटल पेन्शन"],
    "soil_health_card": ["soil health", "soil card", "मृदा स्वास्थ्य", "सॉइल हेल्थ कार्ड", "माती परीक्षण", "माती आरोग्य"],
    "jal_jeevan": ["jal jeevan", "har ghar jal", "water tap", "जल जीवन मिशन", "हर घर जल", "नळ कनेक्शन", "पाणी पुरवठा"],
    "swachh_bharat": ["swachh bharat", "toilet", "शौचालय", "स्वच्छ भारत", "१२०००", "12000", "शौचालय अनुदान"],
    "pm_kusum": ["kusum", "solar pump", "सोलर पंप", "कुसुम योजना", "सौर कृषी पंप", "सौर ऊर्जा पंप"],
    "pm_jan_dhan": ["jan dhan", "pmjdy", "bank account", "जन धन योजना", "झिरो बॅलन्स", "जीरो बैलेंस", "जन धन"],
    "pm_svanidhi": ["svanidhi", "street vendor", "स्वनिधि", "रेहड़ी पटरी", "फेरीवाले", "पीएम स्वनिधि"],
    "pm_svamitva": ["svamitva", "property card", "स्वामित्व", "प्रॉपर्टी कार्ड", "घरपट्टी", "स्वामित्व योजना"],
    "janani_suraksha": ["janani suraksha", "jsy", "जननी सुरक्षा", "प्रसूती सहाय्य", "1400", "माता सुरक्षा"],
    "pmmvy": ["matru vandana", "pmmvy", "मातृ वंदना", "गर्भवती महिला", "5000", "मातृत्व"],
    "enam": ["enam", "mandi", "ई नाम", "बाजार समिती", "मंडी भाव", "ई-नाम"],
    "paramparagat_krishi": ["paramparagat", "organic farming", "जैविक खेती", "सेंद्रिय शेती", "सेंद्रिय खत"],
    "poshan_abhiyaan": ["poshan", "nutrition", "पोषण अभियान", "अंगणवाडी", "कुपोषण", "बाल पोषण"],
    "saubhagya": ["saubhagya", "electricity", "सौभाग्य योजना", "वीज कनेक्शन", "बिजली कनेक्शन"],
    "scholarship": ["scholarship", "nmms", "शिष्यवृत्ती", "स्कॉलरशिप", "विद्यार्थी", "छात्रवृत्ति"],
    "pm_ujala": ["ujala", "led", "उजाला", "एलईडी बल्ब", "उजाला योजना"],
    "pm_jjby": ["jeevan jyoti", "pmjjby", "जीवन ज्योति", "436", "जीवन ज्योती"],
    "pm_sby": ["suraksha bima", "pmsby", "सुरक्षा बीमा", "20", "सुरक्षा विमा"],
    "senior_citizen_savings": ["senior citizen", "वरिष्ठ नागरिक", "ज्येष्ठ नागरिक", "8.2"]
}

def get_smart_context(question: str) -> str:
    """Instant zero-RAM multilingual smart scheme retrieval (<1ms)"""
    schemes = get_all_schemes()
    if not schemes:
        return ""
    
    q_lower = question.lower()
    q_words = [w for w in re.split(r'\W+', q_lower) if len(w) > 1]
    
    scored = []
    for s in schemes:
        sid = s["id"]
        title = s["title"].lower()
        content = s["content"].lower()
        score = 0
        
        # 1. Multilingual keyword matching (Hindi, Marathi, English)
        if sid in SCHEME_KEYWORDS:
            for kw in SCHEME_KEYWORDS[sid]:
                if kw in q_lower:
                    score += len(kw) * 5
                    
        # 2. High priority title word match
        for w in q_words:
            if w in title:
                score += 8
            elif w in content:
                score += 1
                
        # 3. Direct phrase / scheme identifier match
        clean_id = sid.replace("_", " ")
        if clean_id in q_lower or sid in q_lower:
            score += 20
            
        if score > 0:
            scored.append((score, s["content"]))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return "\n\n".join(c for _, c in scored[:3])
    
    # Return top schemes if no keyword matched
    return "\n\n".join(s["content"] for s in schemes[:2])

def get_llm():
    global _LLM
    if _LLM is None:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY environment variable is missing on Render. Please open your Render Dashboard -> Service -> Environment and add GROQ_API_KEY.")
        print("[INFO] Initializing Groq LLM client (openai/gpt-oss-20b)...")
        _LLM = ChatGroq(
            model="openai/gpt-oss-20b",
            groq_api_key=groq_key,
            temperature=0.2,
            max_tokens=900
        )
        print("[INFO] Groq LLM ready!")
    return _LLM

def get_answer(question, preferred_language=None):
    t_start = time.time()
    language = preferred_language if preferred_language else detect_language(question)
    
    llm = get_llm()
    prompt = get_prompt(language)
    context = get_smart_context(question)
    
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})
    elapsed = time.time() - t_start
    print(f"[PERF] Answer generated in {elapsed:.2f}s (Language: {language})")
    return answer, language

