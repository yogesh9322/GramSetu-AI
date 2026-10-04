content = open("rag_pipeline.py", "w", encoding="utf-8")
content.write("""import os
import glob
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def detect_language(text):
    marathi_words = ["काय","कसे","मला","आहे","करा","सांगा","मी","माझे","कुठे","योजनेसाठी","पात्र","द्या","आहेत","करायचे","नाही","त्यांना","कशी","कोण","मिळते","भरावा","लागतो","आपल्या","होते","झाले","करतो"]
    hindi_words = ["क्या","कैसे","मुझे","है","करो","बताओ","मैं","मेरा","कहाँ","होता","करना","मिलता","जाना","लेना","देना","चाहिए","हैं","उनका","उनके","इसके","उसके"]
    mc = sum(1 for w in marathi_words if w in text)
    hc = sum(1 for w in hindi_words if w in text)
    print("Marathi score: " + str(mc) + ", Hindi score: " + str(hc))
    if mc > hc: return "marathi"
    elif hc > 0: return "hindi"
    return "english"

def get_prompt(language):
    if language == "marathi":
        template = \"\"\"तुम्ही एक मदतगार AI सहाय्यक आहात जे महाराष्ट्रातील ग्रामीण लोकांना सरकारी योजनांबद्दल मदत करतात.
खालील माहितीच्या आधारे प्रश्नाचे उत्तर सोप्या मराठीत द्या.
पायरी पायरीने मार्गदर्शन करा. आवश्यक कागदपत्रे आणि हेल्पलाइन नंबर नक्की सांगा.
जर उत्तर माहित नसेल तर सांगा: कृपया जवळच्या CSC केंद्र किंवा ग्रामपंचायतला भेट द्या.
Context: {context}
प्रश्न: {question}
उत्तर (मराठीत):\"\"\"
    elif language == "hindi":
        template = \"\"\"Aap ek helpful AI assistant hain jo rural India ke logon ki madad karte hain.
Context ke aadhar par sawal ka jawab simple Hindi mein dijiye.
Step-by-step guidance dijiye. Documents aur helpline numbers zaroor batayein.
Agar jawab nahi pata: Kripya nazdiki CSC center ya Gram Panchayat jaiye.
Context: {context}
Sawal: {question}
Jawab (Hindi mein):\"\"\"
    else:
        template = \"\"\"You are a helpful AI assistant supporting rural Indian villagers with government schemes.
Answer in simple English based on the context. Give step-by-step guidance.
Always mention required documents and helpline numbers.
If unknown: Please visit your nearest CSC center or Gram Panchayat.
Context: {context}
Question: {question}
Answer (in English):\"\"\"
    return PromptTemplate(template=template, input_variables=["context", "question"])

def load_documents():
    documents = []
    files = glob.glob("../data/*.txt")
    if not files:
        print("No .txt files found in data/ folder!")
        return []
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            documents.append(f.read())
            print("Loaded: " + filepath)
    return documents

def create_vector_db():
    print("Loading documents...")
    docs = load_documents()
    if not docs: return None
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.create_documents(docs)
    print("Created " + str(len(chunks)) + " chunks")
    print("Creating FREE HuggingFace embeddings...")
    embeddings = get_embeddings()
    print("Saving Vector Database...")
    vectordb = FAISS.from_documents(chunks, embeddings)
    vectordb.save_local("../vector_db/schemes_db")
    print("Vector Database created successfully!")
    return vectordb

def load_vector_db():
    return FAISS.load_local(
        "../vector_db/schemes_db",
        get_embeddings(),
        allow_dangerous_deserialization=True
    )

def format_docs(docs):
    return "\\n\\n".join(doc.page_content for doc in docs)

def get_answer(question, preferred_language=None):
    language = preferred_language if preferred_language else detect_language(question)
    print("Detected Language: " + language.upper())
    vectordb = load_vector_db()
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3
    )
    prompt = get_prompt(language)
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt | llm | StrOutputParser()
    )
    return chain.invoke(question), language

if __name__ == "__main__":
    print("=== GramSetu AI - Multilingual RAG Pipeline ===")
    create_vector_db()
    questions = [
        "What is PM Kisan scheme and who is eligible?",
        "MGNREGA job card kaise banaye?",
        "आयुष्मान भारत योजनेसाठी कोण पात्र आहे?"
    ]
    print("\\n=== Testing All 3 Languages ===\\n")
    for q in questions:
        print("Question: " + q)
        ans, lang = get_answer(q)
        print("Language: " + lang.upper())
        print("Answer: " + ans[:300])
        print("-" * 60)
        time.sleep(2)
""")
content.close()
print("rag_pipeline.py written successfully!")