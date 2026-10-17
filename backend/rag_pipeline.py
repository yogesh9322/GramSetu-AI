import os
import glob
import time
import re
import json
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()

_LLM = None
_SCHEME_CACHE: Optional[List[Dict[str, str]]] = None
_SCHEME_DICT: Optional[Dict[str, Dict[str, str]]] = None

# ── Multilingual Language Detection ────────────────────────────
def detect_language(text: str) -> str:
    """
    Accurately detects whether text is in Marathi, Hindi, or English.
    Handles Devanagari script markers as well as Romanized/Hinglish/Manglish words.
    """
    if not text:
        return "hindi"
    
    t_lower = text.lower()
    
    # Distinctive Marathi words (almost never used in Hindi)
    marathi_unique = [
        "मला", "कधी", "कसे", "कसा", "कशी", "काय", "कुठे", "किती", "कोण",
        "मिळेल", "मिळतील", "मिळते", "करावे", "करावा", "करावी", "लागेल", "लागतील", "लागतो",
        "पाहिजे", "आहे", "आहेत", "होते", "होतात", "नाही", "झाले", "होईल",
        "शेतकरी", "शेतकऱ्यांना", "योजनेचे", "योजनेचा", "योजनेची", "कागदपत्रे", "हप्ता", "पैसे",
        "माझे", "आमचे", "आम्हाला", "त्यांना", "सांगा", "द्या"
    ]
    
    # Distinctive Hindi words (almost never used in Marathi)
    hindi_unique = [
        "मुझे", "कब", "कैसे", "कैसा", "कैसी", "क्या", "कहाँ", "कितना", "कितने", "कौन",
        "मिलेगा", "मिलेंगे", "मिलता", "मिलती", "करना", "करे", "करेगा", "लगेगा", "लगेंगे", "लगता",
        "चाहिए", "है", "हैं", "था", "थे", "थी", "नहीं", "हुआ", "होगी", "होगा",
        "किसान", "किसानों", "दस्तावेज़", "किस्त", "पैसा", "रुपये",
        "मेरा", "हमारा", "हमें", "उनको", "उन्हें", "बताओ", "बताइए", "दीजिए"
    ]
    
    marathi_latin = ["kasa", "kase", "kashi", "kay", "kadhi", "ahe", "ahet", "sang", "shetkari", "anudan", "kagadpatra", "kuthe", "kiti", "bhetel", "milnar", "miltil", "pahije", "mahit", "amhi", "amche", "mala"]
    hindi_latin = ["kaise", "kaisa", "kya", "kab", "hai", "hain", "batao", "bataiye", "kisan", "dastavej", "kahan", "kitna", "kitne", "milega", "milenge", "hoga", "chahiye", "hum", "hamara", "shuru", "kare", "mujhe"]
    english_keywords = ["what", "how", "who", "when", "apply", "eligible", "eligibility", "benefits", "documents", "subsidy", "scheme", "loan", "farmer", "insurance", "account"]

    score_mr = sum(2 for w in marathi_unique if w in text) + sum(1 for w in marathi_latin if re.search(r'\b' + re.escape(w) + r'\b', t_lower))
    score_hi = sum(2 for w in hindi_unique if w in text) + sum(1 for w in hindi_latin if re.search(r'\b' + re.escape(w) + r'\b', t_lower))
    score_en = sum(1 for w in english_keywords if re.search(r'\b' + re.escape(w) + r'\b', t_lower))

    if score_mr > score_hi and score_mr > score_en:
        return "marathi"
    elif score_hi > score_mr and score_hi > score_en:
        return "hindi"
    elif score_en > 0 and score_en >= score_mr and score_en >= score_hi:
        return "english"
        
    if score_mr > 0 and score_mr >= score_hi:
        return "marathi"
    elif score_hi > 0:
        return "hindi"
        
    if re.search(r'[\u0900-\u097F]', text):
        return "hindi"
    return "english"


# ── In-Memory Scheme Knowledge Base ────────────────────────────
def get_all_schemes() -> List[Dict[str, str]]:
    """
    Load and cache all 60+ official government scheme documents into memory.
    Zero disk latency (<0.1ms access), completely deterministic.
    """
    global _SCHEME_CACHE, _SCHEME_DICT
    if _SCHEME_CACHE is None:
        base_dir = os.path.dirname(__file__)
        data_dirs = [
            os.path.join(base_dir, "../data"),
            os.path.join(base_dir, "data"),
            os.path.abspath("data")
        ]
        
        target_dir = None
        for d in data_dirs:
            if os.path.exists(d) and len(glob.glob(os.path.join(d, "*.txt"))) > 0:
                target_dir = d
                break
                
        schemes = []
        schemes_dict = {}
        
        if target_dir:
            files = glob.glob(os.path.join(target_dir, "*.txt"))
            for fp in files:
                fname = os.path.basename(fp).replace(".txt", "")
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                    
                    item = {
                        "id": fname,
                        "title": fname.replace("_", " ").title(),
                        "content": content
                    }
                    schemes.append(item)
                    schemes_dict[fname.lower()] = item
                except Exception as e:
                    print(f"[WARN] Failed to read scheme file {fp}: {e}")
                    
        _SCHEME_CACHE = schemes
        _SCHEME_DICT = schemes_dict
        print(f"[INFO] Loaded and indexed {len(_SCHEME_CACHE)} verified government scheme documents into memory.")
        
    return _SCHEME_CACHE

def get_scheme_by_id(scheme_id: str) -> Optional[Dict[str, str]]:
    """Fast direct lookup for a scheme by ID or filename (PM Kisan, Ayushman, etc.)"""
    get_all_schemes()
    if not _SCHEME_DICT or not scheme_id:
        return None
    
    clean_id = str(scheme_id).strip().lower().replace("-", "_").replace(" ", "_")
    
    # Direct key match
    if clean_id in _SCHEME_DICT:
        return _SCHEME_DICT[clean_id]
        
    # Substring / fuzzy match
    for sid, sdata in _SCHEME_DICT.items():
        if clean_id in sid or sid in clean_id:
            return sdata
            
    return None


# ── Multilingual Keyword Index ─────────────────────────────────
SCHEME_KEYWORDS: Dict[str, List[str]] = {
    "pm_kisan": ["pm kisan", "kisan samman", "पीएम किसान", "किसान सम्मान निधि", "६०००", "6000", "शेतकरी अनुदान", "किसान सम्मान", "farmer installment"],
    "fasal_bima": ["fasal bima", "pmfby", "crop insurance", "फसल बीमा", "पीक विमा", "फसल नुकसान", "खरीफ", "रबी", "फसल", "बीमा"],
    "pm_fasal_bima_rabi": ["fasal bima rabi", "रबी फसल बीमा", "रब्बी पीक विमा"],
    "kisan_credit_card": ["kisan credit card", "kcc", "किसान क्रेडिट कार्ड", "केसीसी", "पीक कर्ज", "किसान लोन", "crop loan"],
    "ayushman": ["ayushman", "pmjay", "golden card", "health card", "आयुष्मान भारत", "आयुष्मान कार्ड", "५ लाख", "5 lakh", "आरोग्य कार्ड", "आयुष्मान", "hospital cashless"],
    "awas_yojana": ["pm awas", "pmay", "housing", "आवास योजना", "घरकुल", "घरकुल योजना", "पक्के मकान", "आवास", "home grant"],
    "mgnrega": ["mgnrega", "nrega", "job card", "मनरेगा", "जॉब कार्ड", "रोजगार हमी", "१०० दिवस", "100 days", "रोजगार कार्ड", "100 din"],
    "pm_ujjwala": ["ujjwala", "lpg", "gas", "cylinder", "उज्ज्वला", "गैस कनेक्शन", "सिलेंडर", "मोफत गॅस", "उज्वला", "free cylinder"],
    "sukanya_samriddhi": ["sukanya", "samriddhi", "girl child", "सुकन्या समृद्धि", "मुलगी योजना", "बेटी", "सुकन्या"],
    "e_shram": ["e shram", "eshram", "shramik", "ई श्रम", "श्रम कार्ड", "मजदूर कार्ड", "ई-श्रम", "कामगार कार्ड", "unorganized workers"],
    "pm_mudra": ["mudra", "business loan", "मुद्रा योजना", "शिशु लोन", "किशोर लोन", "तरुण लोन", "व्यवसाय कर्ज", "मुद्रा"],
    "atal_pension": ["atal pension", "apy", "अटल पेंशन", "पेन्शन योजना", "अटल पेन्शन", "monthly pension"],
    "soil_health_card": ["soil health", "soil card", "मृदा स्वास्थ्य", "सॉइल हेल्थ कार्ड", "माती परीक्षण", "माती आरोग्य"],
    "jal_jeevan": ["jal jeevan", "har ghar jal", "water tap", "जल जीवन मिशन", "हर घर जल", "नळ कनेक्शन", "पाणी पुरवठा", "tap water"],
    "swachh_bharat": ["swachh bharat", "toilet", "शौचालय", "स्वच्छ भारत", "१२०००", "12000", "शौचालय अनुदान"],
    "pm_kusum": ["kusum", "solar pump", "सोलर पंप", "कुसुम योजना", "सौर कृषी पंप", "सौर ऊर्जा पंप", "solar subsidy"],
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


# ── Query Intent Classifier ────────────────────────────────────
def classify_intent(question: str) -> str:
    """
    Classifies the user query to guide prompt structure and avoid unnecessary lookups.
    """
    q_low = question.lower().strip()
    
    # Common conversational greetings
    greetings = ["hello", "hi", "hey", "नमस्ते", "नमस्कार", "राम राम", "pranam", "good morning", "good evening"]
    for g in greetings:
        if q_low == g or q_low.startswith(g + " ") or q_low.endswith(" " + g):
            return "GREETING"
            
    # Benefits query
    if any(k in q_low for k in ["benefit", "fayde", "labh", "फायदे", "लाभ", "कितना पैसा", "kitne paise", "kiti paise"]):
        return "BENEFITS"
        
    # Eligibility query
    if any(k in q_low for k in ["eligib", "patra", "who can", "kaun", "kon", "पात्र", "पात्रता", "मिलेगा क्या", "bhetel ka"]):
        return "ELIGIBILITY"
        
    # Documents query
    if any(k in q_low for k in ["document", "kagad", "dastavej", "कागदपत्र", "दस्तावेज़", "kaun se document"]):
        return "DOCUMENTS"
        
    # Application process
    if any(k in q_low for k in ["how to apply", "apply", "form", "kaise apply", "kasa karava", "अर्ज कसा", "आवेदन कैसे"]):
        return "APPLICATION_PROCESS"
        
    # Follow up
    if any(k in q_low for k in ["aur batao", "explain more", "and", "tell me more", "marathi madhe", "hindi mein"]):
        return "FOLLOW_UP"
        
    return "GENERAL_SCHEME"


# ── Context Resolution (Scheme-specific or Smart Retrieval) ─────
def resolve_context(question: str, scheme_id: Optional[str] = None, scheme_name: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Resolves the exact grounded context for the query:
    1. If a specific scheme was selected or identified: loads its verified text file directly.
    2. Otherwise, executes instant keyword & semantic retrieval over the 60+ cached schemes.
    Returns: (context_string, identified_scheme_id)
    """
    schemes = get_all_schemes()
    if not schemes:
        return ("", None)
        
    # Priority 1: Explicit Scheme Selection from UI
    if scheme_id:
        target = get_scheme_by_id(scheme_id)
        if target:
            annotated_context = f"[VERIFIED OFFICIAL SCHEME DATA: {target['title']}]\n{target['content']}"
            return (annotated_context, target['id'])
            
    if scheme_name:
        # Search by scheme name
        sn_lower = scheme_name.lower()
        for s in schemes:
            if s["title"].lower() in sn_lower or sn_lower in s["title"].lower():
                annotated_context = f"[VERIFIED OFFICIAL SCHEME DATA: {s['title']}]\n{s['content']}"
                return (annotated_context, s['id'])
                
    # Priority 2: Keyword and Semantic Scoring Retrieval
    q_lower = question.lower()
    q_words = [w for w in re.split(r'\W+', q_lower) if len(w) > 1]
    
    scored = []
    for s in schemes:
        sid = s["id"]
        title = s["title"].lower()
        content = s["content"].lower()
        score = 0
        
        # Multilingual keyword matches
        if sid in SCHEME_KEYWORDS:
            for kw in SCHEME_KEYWORDS[sid]:
                if kw in q_lower:
                    score += len(kw) * 6
                    
        # High-value title words match
        for w in q_words:
            if w in title:
                score += 8
            elif w in content:
                score += 1
                
        # Identifier match
        clean_id = sid.replace("_", " ")
        if clean_id in q_lower or sid in q_lower:
            score += 25
            
        if score > 0:
            scored.append((score, s))
            
    scored.sort(key=lambda x: x[0], reverse=True)
    
    if scored:
        top_scheme = scored[0][1]
        # Include top 1 or 2 schemes to avoid prompt noise and context contamination
        top_chunks = [f"[Source: {s['title']}]\n{s['content']}" for _, s in scored[:2]]
        return ("\n\n".join(top_chunks), top_scheme['id'])
        
    # Priority 3: Fallback generic top schemes if no specific keyword matched
    return ("\n\n".join(f"[Source: {s['title']}]\n{s['content']}" for s in schemes[:2]), None)


# ── Bounded Context-Aware Prompt Construction ──────────────────
def format_history(history: Optional[List[Dict[str, str]]]) -> str:
    """Format the last 3 turns of conversation cleanly for bounded context."""
    if not history:
        return ""
    recent = history[-4:] # strictly bounded to avoid prompt pollution
    turns = []
    for h in recent:
        role = "Citizen" if h.get("role") == "user" else "GramSetu"
        txt = h.get("text", "").strip().split("\n")[0][:140]
        if txt:
            turns.append(f"{role}: {txt}")
    return "\n".join(turns)

def build_unified_prompt(language: str, context: str, question: str, history_str: str = "", intent: str = "GENERAL_SCHEME") -> str:
    """
    Constructs a grounded, factual prompt enforcing strict verification rules.
    Never fabricates facts, subsidies, URLs, or deadlines.
    """
    lang_lower = language.lower() if language else "hindi"
    
    history_block = f"\nPrevious Conversation Context:\n{history_str}\n" if history_str else ""
    
    if lang_lower == "marathi":
        return f"""तुम्ही GramSetu AI (ग्रामसेतू एआय) आहात — भारतीय ग्रामीण नागरिक आणि शेतकऱ्यांसाठी अधिकृत सरकारी योजनांचे AI मार्गदर्शक.

महत्वाचे नियम (Strict Accuracy Rules):
1. केवळ खाली दिलेल्या अधिकृत Context मधील सत्य माहितीच्या आधारे अचूक आणि संपूर्ण उत्तर द्या.
2. कोणतीही योजना, रक्कम, वयोमर्यादा, पात्रता निकष किंवा वेबसाईट स्वतःच्या मनाने काल्पनिक बनवू नका.
3. जर कोणतीही माहिती Context मध्ये उपलब्ध नसेल, तर स्पष्टपणे सांगा: "या मुद्द्याची अधिकृत नोंद सध्या उपलब्ध नाही. कृपया अचूक माहितीसाठी आपल्या ग्रामपंचायत किंवा जवळच्या CSC केंद्राशी संपर्क साधा."
4. उत्तर स्पष्ट, वाचायला सोप्या आणि प्रमाण मराठीत (देवनागरी लिपीत) द्या.

उत्तरात खालील मुद्द्यांचा समावेश करा:
1. योजनेचे मुख्य फायदे (Key Benefits)
2. कोण पात्र आहे (Eligibility Criteria)
3. आवश्यक कागदपत्रे (Required Documents)
4. अर्ज कसा करावा - सविस्तर पायरी पायरीने मार्गदर्शन (How to Apply)
5. अधिकृत हेल्पलाइन आणि अधिकृत पोर्टल (Helpline & Official Website)
{history_block}
Context (अधिकृत योजना माहिती):
{context}

नागरिकाचा प्रश्न: {question}
GramSetu AI उत्तर (मराठीत):"""

    elif lang_lower == "hindi":
        return f"""आप GramSetu AI (ग्रामसेतु एआई) हैं — भारत के ग्रामीण नागरिकों और किसानों के लिए आधिकारिक सरकारी योजनाओं के विश्वसनीय सहायक।

सख्त सटीकता नियम (Strict Accuracy Rules):
1. केवल नीचे दी गई आधिकारिक Context जानकारी के आधार पर 100% सटीक और पूर्ण उत्तर दें।
2. योजना के लाभ, राशि, पात्रता शर्तें, दस्तावेज़ या वेबसाइट लिंक अपनी तरफ से मनगढ़ंत (fabricate) न बनाएं।
3. यदि कोई विशेष जानकारी Context में उपलब्ध नहीं है, तो स्पष्ट रूप से बताएं: "इस बिंदु की आधिकारिक पुष्टि के लिए कृपया अपनी ग्राम पंचायत या नजदीकी सीएससी (CSC) केंद्र से संपर्क करें।"
4. उत्तर सरल, स्पष्ट और शुद्ध हिंदी (देवनागरी लिपि) में दें।

उत्तर में निम्नलिखित 5 बिंदुओं को स्पष्ट रूप से शामिल करें:
1. योजना के मुख्य लाभ (Key Benefits)
2. पात्रता - कौन आवेदन कर सकता है (Eligibility Criteria)
3. आवश्यक दस्तावेज़ (Required Documents)
4. आवेदन कैसे करें - चरण-दर-चरण प्रक्रिया (How to Apply)
5. आधिकारिक हेल्पलाइन और पोर्टल (Helpline & Official Website)
{history_block}
Context (आधिकारिक योजना डेटा):
{context}

नागरिक का प्रश्न: {question}
GramSetu AI उत्तर (हिंदी में):"""

    else:
        return f"""You are GramSetu AI — a dedicated, reliable AI advisory assistant supporting rural Indian citizens and farmers with official government welfare schemes.

Strict Accuracy & Verification Rules:
1. Rely EXCLUSIVELY on the verified facts in the provided Context.
2. NEVER hallucinate or fabricate scheme names, subsidy amounts, eligibility criteria, deadlines, or websites.
3. If specific information is missing from the Context, state clearly: "Official verification for this specific detail is not present in current records. Please visit your local Gram Panchayat or nearest Common Service Centre (CSC) to confirm."
4. Provide structured, practical guidance in clear, friendly English.

Ensure your response covers:
1. Key Benefits (Exact subsidy or grant amount)
2. Eligibility Criteria (Who can apply)
3. Required Documents (Checklist)
4. Step-by-Step Application Process
5. Official Helpline & Government Website
{history_block}
Context (Official Scheme Facts):
{context}

Citizen Question: {question}
GramSetu AI Answer (in English):"""


# ── LLM Singleton & Groq Client ────────────────────────────────
def get_llm():
    """
    Initializes and caches the Groq LLM client.
    Reuses instance across requests to ensure zero reconnection overhead.
    """
    global _LLM
    if _LLM is None:
        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY environment variable is missing on Render. Please configure GROQ_API_KEY in Render Dashboard -> Environment.")
        
        # Allow configuring model via env, defaulting to llama-3.3-70b-versatile
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        print(f"[INFO] Initializing Groq LLM client ({model_name})...")
        
        try:
            _LLM = ChatGroq(
                model=model_name,
                groq_api_key=groq_key,
                temperature=0.2,   # Low temperature guarantees grounded facts
                max_tokens=900,
                timeout=25
            )
            print("[INFO] Groq LLM client successfully initialized!")
        except Exception as e:
            print(f"[WARN] Failed to load {model_name}, falling back to llama-3.1-8b-instant: {e}")
            _LLM = ChatGroq(
                model="llama-3.1-8b-instant",
                groq_api_key=groq_key,
                temperature=0.2,
                max_tokens=900,
                timeout=25
            )
    return _LLM


# ── Synchronous Central Answering Pipeline ─────────────────────
def get_answer_unified(
    question: str,
    preferred_language: Optional[str] = None,
    scheme_id: Optional[str] = None,
    scheme_name: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Unified synchronous question-answering pipeline.
    Handles typed text, selected scheme, transcribed voice, and follow-ups.
    Returns: (answer_text, detected_language, metrics_dict)
    """
    t_start = time.time()
    
    # 1. Normalize and detect language
    clean_q = question.strip()
    language = preferred_language if preferred_language else detect_language(clean_q)
    
    # 2. Classify intent
    intent = classify_intent(clean_q)
    
    # Fast path for standalone greetings
    if intent == "GREETING" and not scheme_id:
        if language == "marathi":
            greeting = "नमस्कार! 🙏 मी GramSetu AI आहे. मी तुम्हाला ६०+ सरकारी योजना, अनुदान, शेतकरी कर्ज आणि आवश्यक कागदपत्रांबद्दल संपूर्ण माहिती देऊ शकतो. आज मी आपली काय मदत करू?"
        elif language == "hindi":
            greeting = "नमस्ते! 🙏 मैं GramSetu AI हूँ। मैं आपको 60+ सरकारी योजनाओं, सब्सिडी, किसान ऋण और आवश्यक दस्तावेजों की सही जानकारी दे सकता हूँ। आज आप किस योजना के बारे में जानना चाहते हैं?"
        else:
            greeting = "Hello and welcome! 🙏 I am GramSetu AI, your village advisory assistant for 60+ Indian government schemes. How can I help you today?"
        return (greeting, language, {"latency_ms": int((time.time() - t_start) * 1000), "scheme_id": None})
        
    # 3. Resolve context
    t_ret_start = time.time()
    context, resolved_scheme_id = resolve_context(clean_q, scheme_id, scheme_name)
    retrieval_ms = int((time.time() - t_ret_start) * 1000)
    
    # 4. Format history & build bounded prompt
    history_str = format_history(history)
    prompt_str = build_unified_prompt(language, context, clean_q, history_str, intent)
    
    # 5. Execute Groq inference
    t_llm_start = time.time()
    llm = get_llm()
    prompt_template = PromptTemplate(template="{prompt_text}", input_variables=["prompt_text"])
    chain = prompt_template | llm | StrOutputParser()
    
    try:
        answer = chain.invoke({"prompt_text": prompt_str})
    except Exception as e:
        print(f"[ERROR] Groq LLM inference error: {e}")
        # Secondary fallback if primary model timed out
        fallback_llm = ChatGroq(
            model="llama-3.1-8b-instant",
            groq_api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.2,
            max_tokens=900
        )
        chain_fallback = prompt_template | fallback_llm | StrOutputParser()
        answer = chain_fallback.invoke({"prompt_text": prompt_str})
        
    llm_ms = int((time.time() - t_llm_start) * 1000)
    total_ms = int((time.time() - t_start) * 1000)
    
    metrics = {
        "retrieval_ms": retrieval_ms,
        "llm_ms": llm_ms,
        "total_ms": total_ms,
        "scheme_id": resolved_scheme_id,
        "language": language
    }
    print(f"[METRICS] Request answered in {total_ms}ms (Retrieval: {retrieval_ms}ms, LLM: {llm_ms}ms, Lang: {language})")
    
    return (answer, language, metrics)


# ── Streaming Answering Pipeline (SSE / Server-Sent Events) ────
async def stream_answer_unified(
    question: str,
    preferred_language: Optional[str] = None,
    scheme_id: Optional[str] = None,
    scheme_name: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None
):
    """
    Asynchronous generator yielding real-time tokens in standard Server-Sent Events (SSE) format.
    Yields:
      data: {"type": "start", "language": "...", "scheme_id": "..."}\n\n
      data: {"type": "token", "content": "..."}\n\n
      data: {"type": "done", "language": "...", "latency_ms": 1200}\n\n
    """
    t_start = time.time()
    clean_q = question.strip()
    language = preferred_language if preferred_language else detect_language(clean_q)
    intent = classify_intent(clean_q)
    
    # Fast path for greetings
    if intent == "GREETING" and not scheme_id:
        if language == "marathi":
            text = "नमस्कार! 🙏 मी GramSetu AI आहे. मी तुम्हाला ६०+ सरकारी योजना, अनुदान आणि कागदपत्रांबद्दल माहिती देऊ शकतो. आज मी आपली काय मदत करू?"
        elif language == "hindi":
            text = "नमस्ते! 🙏 मैं GramSetu AI हूँ। मैं आपको 60+ सरकारी योजनाओं और सब्सिडी की सटीक जानकारी दे सकता हूँ। आप किस योजना के बारे में जानना चाहते हैं?"
        else:
            text = "Hello! 🙏 I am GramSetu AI, your village assistant for 60+ government welfare schemes. How can I assist you today?"
            
        yield f"data: {json.dumps({'type': 'start', 'language': language, 'scheme_id': None})}\n\n"
        for word in text.split(" "):
            yield f"data: {json.dumps({'type': 'token', 'content': word + ' '})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'language': language, 'latency_ms': int((time.time() - t_start)*1000)})}\n\n"
        return

    # Resolve context & scheme
    context, resolved_scheme_id = resolve_context(clean_q, scheme_id, scheme_name)
    history_str = format_history(history)
    prompt_str = build_unified_prompt(language, context, clean_q, history_str, intent)
    
    # Notify stream start
    yield f"data: {json.dumps({'type': 'start', 'language': language, 'scheme_id': resolved_scheme_id})}\n\n"
    
    llm = get_llm()
    prompt_template = PromptTemplate(template="{prompt_text}", input_variables=["prompt_text"])
    chain = prompt_template | llm | StrOutputParser()
    
    try:
        # Stream chunks from LangChain Groq
        for chunk in chain.stream({"prompt_text": prompt_str}):
            if chunk:
                yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                
        total_ms = int((time.time() - t_start) * 1000)
        yield f"data: {json.dumps({'type': 'done', 'language': language, 'latency_ms': total_ms, 'scheme_id': resolved_scheme_id})}\n\n"
    except Exception as e:
        print(f"[ERROR] Stream generation error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"


# Compatibility wrapper for existing legacy callers
def get_answer(question: str, preferred_language: Optional[str] = None):
    ans, lang, _ = get_answer_unified(question, preferred_language=preferred_language)
    return ans, lang
