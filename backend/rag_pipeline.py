import os
import glob
import time
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq

load_dotenv()

_EMBEDDINGS = None
_VECTOR_DB = None
_LLM = None

def get_embeddings():
    global _EMBEDDINGS
    if _EMBEDDINGS is None:
        print("[INFO] Loading HuggingFace Embeddings model into memory...")
        _EMBEDDINGS = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        print("[INFO] Embeddings model loaded!")
    return _EMBEDDINGS

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

def load_documents():
    documents = []
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    files = glob.glob(os.path.join(data_dir, "*.txt"))
    if not files:
        print("[WARN] No .txt files found in data/ folder!")
        return []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            documents.append(f.read())
    return documents

def create_vector_db():
    print("[INFO] Loading documents...")
    docs = load_documents()
    if not docs: return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_documents(docs)
    print(f"[INFO] Created {len(chunks)} chunks")
    print("[INFO] Creating HuggingFace embeddings...")
    embeddings = get_embeddings()
    print("[INFO] Saving Vector Database...")
    db_path = os.path.join(os.path.dirname(__file__), "../vector_db/schemes_db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    vectordb = FAISS.from_documents(chunks, embeddings)
    vectordb.save_local(db_path)
    print("[INFO] Vector Database created successfully!")
    return vectordb

def load_vector_db():
    global _VECTOR_DB
    if _VECTOR_DB is None:
        db_path = os.path.join(os.path.dirname(__file__), "../vector_db/schemes_db")
        if not os.path.exists(db_path):
            print("[WARN] Vector DB not found, creating new one...")
            create_vector_db()
        print("[INFO] Loading FAISS Vector DB into memory...")
        _VECTOR_DB = FAISS.load_local(
            db_path,
            get_embeddings(),
            allow_dangerous_deserialization=True
        )
        print("[INFO] FAISS Vector DB loaded into memory!")
    return _VECTOR_DB

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

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def get_fallback_context(question: str) -> str:
    """Instant direct scheme context retrieval from data/*.txt (zero RAM overhead, 100% reliable)"""
    data_dir = os.path.join(os.path.dirname(__file__), "../data")
    files = glob.glob(os.path.join(data_dir, "*.txt"))
    if not files:
        return ""
    
    q_words = [w.lower() for w in question.split() if len(w) > 2]
    scored = []
    for fp in files:
        fname = os.path.basename(fp).lower()
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            score = sum(4 for w in q_words if w in fname) + sum(1 for w in q_words if w in content.lower())
            if score > 0:
                scored.append((score, content))
        except Exception:
            pass
            
    scored.sort(key=lambda x: x[0], reverse=True)
    if scored:
        return "\n\n".join(c for _, c in scored[:3])
    
    # If no keyword matched, return top scheme
    try:
        with open(files[0], "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def get_answer(question, preferred_language=None):
    t_start = time.time()
    language = preferred_language if preferred_language else detect_language(question)
    
    llm = get_llm()
    prompt = get_prompt(language)
    context = ""

    # 1. Try FAISS Vector DB retrieval
    try:
        vectordb = load_vector_db()
        if vectordb:
            retriever = vectordb.as_retriever(search_kwargs={"k": 3})
            docs = retriever.invoke(question)
            context = format_docs(docs)
    except Exception as e:
        print(f"[WARN] FAISS retrieval notice: {e}, using direct scheme context...")

    # 2. If vector DB returned empty or wasn't ready, use instant direct scheme context
    if not context.strip():
        context = get_fallback_context(question)
    
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke({"context": context, "question": question})
    elapsed = time.time() - t_start
    print(f"[PERF] Answer generated in {elapsed:.2f}s (Language: {language})")
    return answer, language
