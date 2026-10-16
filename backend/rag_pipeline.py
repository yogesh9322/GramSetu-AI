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
खालील माहितीच्या (Context) आधारे विचारलेल्या प्रश्नाचे संपूर्ण, सविस्तर आणि अचूक उत्तर सोप्या मराठीत (देवनागरी लिपीत) द्या.
खालील मुद्द्यांचा स्पष्ट समावेश करा:
1. योजनेचे मुख्य फायदे (Key Benefits)
2. कोण पात्र आहे (Eligibility)
3. आवश्यक कागदपत्रे (Required Documents)
4. अर्ज कसा करावा - सविस्तर पायरी पायरीने मार्गदर्शन (How to Apply)
5. हेल्पलाइन नंबर आणि अधिकृत पोर्टल (Helpline & Official Website)

जर उत्तर माहितीमध्ये नसेल तर सांगा: कृपया जवळच्या CSC केंद्र किंवा ग्रामपंचायतला भेट द्या.
Context: {context}
प्रश्न: {question}
उत्तर (मराठीत):"""
    elif language == "hindi":
        template = """आप एक मददगार AI सहायक हैं जो भारत के ग्रामीण नागरिकों को सरकारी योजनाओं की पूरी जानकारी देते हैं।
नीचे दी गई जानकारी (Context) के आधार पर प्रश्न का संपूर्ण, विस्तृत और स्पष्ट उत्तर हिंदी (देवनागरी लिपि) में दें।
उत्तर में निम्नलिखित सभी बिंदुओं को स्पष्ट रूप से शामिल करें:
1. योजना के मुख्य लाभ (Key Benefits)
2. पात्रता - कौन आवेदन कर सकता है (Eligibility)
3. आवश्यक दस्तावेज़ (Required Documents)
4. आवेदन कैसे करें - चरण-दर-चरण प्रक्रिया (How to Apply)
5. हेल्पलाइन नंबर और आधिकारिक पोर्टल (Helpline & Official Website)

यदि उत्तर जानकारी में न मिले तो कहें: कृपया नजदीकी CSC केंद्र या ग्राम पंचायत से संपर्क करें।
Context: {context}
प्रश्न: {question}
उत्तर (हिंदी में):"""
    else:
        template = """You are a helpful AI assistant supporting rural Indian citizens with government schemes.
Provide a complete, comprehensive, and detailed answer in clear English based on the provided context.
Include all key details:
1. Main Benefits
2. Eligibility Criteria
3. Required Documents
4. Step-by-Step Application Process
5. Helpline Number & Official Website

If unknown: Please visit your nearest CSC center or Gram Panchayat.
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

def get_smart_context(question: str) -> str:
    """Instant zero-RAM smart scheme retrieval (<1ms)"""
    schemes = get_all_schemes()
    if not schemes:
        return ""
    
    q_lower = question.lower()
    q_words = [w for w in re.split(r'\W+', q_lower) if len(w) > 1]
    
    scored = []
    for s in schemes:
        title = s["title"].lower()
        content = s["content"].lower()
        score = 0
        
        # High priority title word match
        for w in q_words:
            if w in title:
                score += 8
            elif w in content:
                score += 1
                
        # Direct phrase / scheme identifier match
        clean_id = s["id"].replace("_", " ")
        if clean_id in q_lower or s["id"] in q_lower:
            score += 15
            
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

