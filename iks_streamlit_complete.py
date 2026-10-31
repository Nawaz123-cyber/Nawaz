"""Bharatiya Jnana Parampara - complete Streamlit conversion.
Run: pip install streamlit pandas networkx && streamlit run iks_streamlit_complete.py
All data and algorithms are ported from the supplied source_code.zip.
"""
import csv, io, json, random, sqlite3, time, unicodedata
from pathlib import Path
import pandas as pd
import streamlit as st

# ============================= catalogue.py =============================
CATALOGUE = [
 {"id":"IKS-001","title":"Rigveda","script":"Devanagari","creator":"Traditional Vedic rishis","period":"c. 1500–1200 BCE (approx.)","domain":"Vedic literature"},
 {"id":"IKS-002","title":"Arthashastra","script":"Devanagari","creator":"Kautilya (traditional attribution)","period":"date and layers debated","domain":"Statecraft and economics"},
 {"id":"IKS-003","title":"Charaka Samhita","script":"Devanagari","creator":"Charaka (traditional attribution)","period":"composite text; dates debated","domain":"Ayurveda and medicine"},
 {"id":"IKS-004","title":"Sushruta Samhita","script":"Devanagari","creator":"Sushruta (traditional attribution)","period":"composite text; dates debated","domain":"Ayurveda and surgery"},
 {"id":"IKS-005","title":"Aryabhatiya","script":"Devanagari","creator":"Aryabhata","period":"499 CE","domain":"Mathematics and astronomy"},
 {"id":"IKS-006","title":"Brahmasphutasiddhanta","script":"Devanagari","creator":"Brahmagupta","period":"628 CE","domain":"Mathematics and astronomy"},
 {"id":"IKS-007","title":"Ashtadhyayi","script":"Devanagari","creator":"Panini","period":"c. 5th–4th century BCE (approx.)","domain":"Grammar and linguistics"},
 {"id":"IKS-008","title":"Lilavati","script":"Devanagari","creator":"Bhaskaracharya","period":"12th century CE","domain":"Mathematics"},
 {"id":"IKS-009","title":"Natyashastra","script":"Devanagari","creator":"Bharata Muni (traditional attribution)","period":"composite text; dates debated","domain":"Performing arts"},
 {"id":"IKS-010","title":"Yoga Sutras","script":"Devanagari","creator":"Patanjali (traditional attribution)","period":"date debated","domain":"Philosophy and yoga"},
 {"id":"IKS-011","title":"Sulba Sutras","script":"Devanagari","creator":"Baudhayana and other authors","period":"early first millennium BCE (approx.)","domain":"Geometry"},
 {"id":"IKS-012","title":"Vaisheshika Sutra","script":"Devanagari","creator":"Kanada (traditional attribution)","period":"date debated","domain":"Natural philosophy"}
]

def export_catalogue(folder="outputs"):
    folder=Path(folder); folder.mkdir(exist_ok=True)
    (folder/"catalogue.json").write_text(json.dumps(CATALOGUE,ensure_ascii=False,indent=2),encoding="utf-8")
    with (folder/"catalogue.csv").open("w",newline="",encoding="utf-8-sig") as f:
        writer=csv.DictWriter(f,fieldnames=CATALOGUE[0].keys()); writer.writeheader(); writer.writerows(CATALOGUE)
    return len(CATALOGUE)

# ========================== transliteration.py ==========================
VOWELS={"अ":"a","आ":"ā","इ":"i","ई":"ī","उ":"u","ऊ":"ū","ऋ":"ṛ","ए":"e","ऐ":"ai","ओ":"o","औ":"au"}
MATRAS={"ा":"ā","ि":"i","ी":"ī","ु":"u","ू":"ū","ृ":"ṛ","े":"e","ै":"ai","ो":"o","ौ":"au"}
CONS={"क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"ṅ","च":"c","छ":"ch","ज":"j","झ":"jh","ञ":"ñ","ट":"ṭ","ठ":"ṭh","ड":"ḍ","ढ":"ḍh","ण":"ṇ","त":"t","थ":"th","द":"d","ध":"dh","न":"n","प":"p","फ":"ph","ब":"b","भ":"bh","म":"m","य":"y","र":"r","ल":"l","व":"v","श":"ś","ष":"ṣ","स":"s","ह":"h"}
VIRAMA="्"
OTHER={"ं":"ṃ","ः":"ḥ","ँ":"m̐","ऽ":"’","ॐ":"oṃ","।":"।","॥":"॥"}
def to_iast(text):
    result=[]; i=0
    while i<len(text):
        ch=text[i]
        if ch in CONS:
            result.append(CONS[ch]); nxt=text[i+1] if i+1<len(text) else ""
            if nxt==VIRAMA: i+=2; continue
            if nxt in MATRAS: result.append(MATRAS[nxt]); i+=2; continue
            result.append("a")
        elif ch in VOWELS: result.append(VOWELS[ch])
        elif ch in MATRAS: result.append(MATRAS[ch])
        elif ch in OTHER: result.append(OTHER[ch])
        else: result.append(ch)
        i+=1
    return "".join(result)

# =========================== search_engine.py ===========================
CORPUS=[
 ("V-01","Rigveda 3.62.10","ॐ भूर्भुवः स्वः तत्सवितुर्वरेण्यं भर्गो देवस्य धीमहि धियो यो नः प्रचोदयात्"),
 ("V-02","Bhagavad Gita 2.47","कर्मण्येवाधिकारस्ते मा फलेषु कदाचन । मा कर्मफलहेतुर्भूर्मा ते सङ्गोऽस्त्वकर्मणि ॥"),
 ("V-03","Yoga Sutra 1.2","योगश्चित्तवृत्तिनिरोधः"),
 ("V-04","Isha Upanishad 1","ईशावास्यमिदं सर्वं यत्किञ्च जगत्यां जगत्"),
 ("V-05","Brihadaranyaka Upanishad 1.3.28","असतो मा सद्गमय तमसो मा ज्योतिर्गमय मृत्योर्मामृतं गमय")]
def fold(text):
    text=unicodedata.normalize("NFD",text.lower()); text="".join(c for c in text if not unicodedata.combining(c))
    return text.replace("ṇ","n").replace("ṃ","m").replace("ḥ","h").replace("ś","s").replace("ṣ","s").replace("ṭ","t").replace("ḍ","d").replace("ṛ","r")
def search(query):
    q=fold(query.strip())
    if not q:return []
    found=[]
    for ident,source,devanagari in CORPUS:
        roman=to_iast(devanagari)
        if q in fold(roman):found.append((ident,source,devanagari,roman))
    return found

# ========================== ocr_evaluation.py ==========================
CONFUSIONS={"ब":"व","व":"ब","घ":"ध","ध":"घ","म":"भ","भ":"म","ट":"ठ","ठ":"ट","न":"ण","ण":"न","स":"श","श":"स"}
def distance(a,b):
    prev=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        cur=[i]
        for j,y in enumerate(b,1):cur.append(min(prev[j]+1,cur[-1]+1,prev[j-1]+(x!=y)))
        prev=cur
    return prev[-1]
def cer(ref,hyp):return distance(ref,hyp)/max(1,len(ref))
def wer(ref,hyp):return distance(ref.split(),hyp.split())/max(1,len(ref.split()))
def noise(text,rate,seed=9):
    rng=random.Random(seed); out=[]
    for ch in text:
        if ch in CONFUSIONS and rng.random()<rate:out.append(CONFUSIONS[ch])
        elif ch!=" " and rng.random()<rate/10:continue
        else:out.append(ch)
    return "".join(out)
def evaluate(rate):
    refs=[x[2] for x in CORPUS]; hyps=[noise(x,rate,9+i) for i,x in enumerate(refs)]
    return (sum(cer(a,b) for a,b in zip(refs,hyps))/len(refs),sum(wer(a,b) for a,b in zip(refs,hyps))/len(refs))

# ========================== knowledge_graph.py =========================
CONCEPTS={"Ashtadhyayi":"Rule-based grammar","Aryabhatiya":"Mathematical computation","Brahmasphutasiddhanta":"Arithmetic and zero","Sulba Sutras":"Geometrical construction","Yoga Sutras":"Structured philosophical concepts","Sushruta Samhita":"Organised procedural knowledge"}
def build_graph():
    try:
        import networkx as nx
    except ImportError:
        nx=None
    if nx:
        graph=nx.DiGraph()
        for item in CATALOGUE:
            title=item["title"]; author=item["creator"]; domain=item["domain"]
            graph.add_node(title,kind="text"); graph.add_node(author,kind="author"); graph.add_node(domain,kind="domain")
            graph.add_edge(title,author,relation="attributed_to"); graph.add_edge(title,domain,relation="belongs_to")
        for title,concept in CONCEPTS.items():graph.add_node(concept,kind="computational concept"); graph.add_edge(title,concept,relation="illustrates")
        return graph
    # Fallback edge list retains the graph data if networkx is not installed.
    edges=[]
    for item in CATALOGUE:
        edges += [(item['title'],item['creator'],'attributed_to'),(item['title'],item['domain'],'belongs_to')]
    edges += [(a,b,'illustrates') for a,b in CONCEPTS.items()]
    return edges

def graph_edges():
    g=build_graph()
    if isinstance(g,list):return g
    return [(a,b,d.get('relation','')) for a,b,d in g.edges(data=True)]

# ============================= archive_db.py ===========================
def build_db():
    db=sqlite3.connect(":memory:")
    db.executescript("""
    CREATE TABLE Author(AuthorID INTEGER PRIMARY KEY, Name TEXT, Era TEXT);
    CREATE TABLE Manuscript(ManuscriptID INTEGER PRIMARY KEY, Title TEXT, Language TEXT, Script TEXT, Category TEXT, AuthorID INTEGER REFERENCES Author(AuthorID));
    CREATE TABLE Digitization(DigitizationID INTEGER PRIMARY KEY, ManuscriptID INTEGER UNIQUE REFERENCES Manuscript(ManuscriptID), ScanDate TEXT, Format TEXT, Resolution TEXT);
    CREATE TABLE Repository(RepositoryID INTEGER PRIMARY KEY, Name TEXT, Location TEXT, DigitizationID INTEGER REFERENCES Digitization(DigitizationID));
    CREATE TABLE User(UserID INTEGER PRIMARY KEY, Name TEXT, AccessLevel TEXT);
    """)
    authors=[(1,"Charaka","Ancient"),(2,"Sushruta","Ancient"),(3,"Vagbhata","Classical"),(4,"Unknown","Unknown"),(5,"Kautilya","Mauryan")]
    manus=[(1,"Charaka Samhita","Sanskrit","Devanagari","Ayurveda",1),(2,"Sushruta Samhita","Sanskrit","Devanagari","Ayurveda",2),(3,"Ashtanga Hridayam","Sanskrit","Devanagari","Ayurveda",3),(4,"Surya Siddhanta","Sanskrit","Devanagari","Astronomy",4),(5,"Arthashastra (Excerpt)","Sanskrit","Devanagari","Governance",5)]
    digi=[(1,1,"2026-08-10","PDF / OCR-Text","600 dpi"),(2,2,"2026-08-11","Image / TIFF","600 dpi"),(3,3,"2026-08-12","PDF","300 dpi"),(4,4,"2026-08-13","Scanned Image","400 dpi"),(5,5,"2026-08-14","PDF / OCR-Text","600 dpi")]
    db.executemany("INSERT INTO Author VALUES(?,?,?)",authors); db.executemany("INSERT INTO Manuscript VALUES(?,?,?,?,?,?)",manus)
    db.executemany("INSERT INTO Digitization VALUES(?,?,?,?,?)",digi)
    db.executemany("INSERT INTO Repository VALUES(?,?,?,?)",[(d[0],"BJP Digital Archive","Server-1",d[0]) for d in digi])
    db.executemany("INSERT INTO User VALUES(?,?,?)",[(1,"Researcher","Full"),(2,"Student","Read"),(3,"Public","Read")])
    return db
def search_db(db,keyword):
    start=time.perf_counter(); like=f"%{keyword}%"
    rows=db.execute("""SELECT 'DR-' || printf('%03d',m.ManuscriptID),m.Title,a.Name,m.Language,d.Format,m.Category
    FROM Manuscript m JOIN Author a ON a.AuthorID=m.AuthorID JOIN Digitization d ON d.ManuscriptID=m.ManuscriptID
    WHERE m.Title LIKE ? OR a.Name LIKE ? OR m.Language LIKE ? OR m.Category LIKE ? ORDER BY m.ManuscriptID""",(like,)*4).fetchall()
    return rows,time.perf_counter()-start

# ============================ Streamlit UI =============================
st.set_page_config(page_title="Bharatiya Jnana Parampara - Digital Archive",page_icon="📜",layout="wide")
st.markdown("""<style>
.stApp{background:#f3efe6;color:#2a2220}.block-container{padding-top:2rem}
[data-testid="stSidebar"]{background:#e9dfd1}h1,h2,h3{color:#780d0d}
div[data-testid="stMetric"]{background:#fffdf8;border:1px solid #d9cfc0;padding:12px;border-radius:9px}
.stButton>button{border-radius:7px}
</style>""",unsafe_allow_html=True)
st.title("BHARATIYA JNANA PARAMPARA")
st.subheader("DIGITIZATION PROTOTYPE")
st.caption("Project: Digitization of the Bharatiya Jnana Parampara | Subject: Indian Knowledge Systems")
PAGES=["Home / Run All", "Digital Manuscript Catalogue", "Devanagari to IAST", "Search Digitized Sanskrit Text", "Synthetic OCR Evaluation", "Knowledge Graph", "SQLite Archive Database", "Web Search Interface"]
page=st.sidebar.radio("Select Module",PAGES)
st.sidebar.markdown("---")
st.sidebar.caption("Complete Streamlit conversion of the supplied multi-file Python project and prototype.html.")

if page=="Home / Run All":
    st.header("Complete Prototype - Main Program Output")
    st.write("This page reproduces the sequence of operations performed by `main.py all`.")
    if st.button("▶ Run Complete Prototype",type="primary"):
        st.markdown("### BHARATIYA JNANA PARAMPARA — DIGITIZATION PROTOTYPE")
        st.markdown("#### 1. CATALOGUE")
        st.write("Records:",export_catalogue())
        for x in CATALOGUE[:5]:st.code(f"{x['id']} | {x['title']} | {x['domain']}")
        st.markdown("#### 2. TRANSLITERATION")
        for x in CORPUS[:3]:
            st.write(x[1]); st.code(x[2]); st.code(to_iast(x[2]))
        st.markdown("#### 3. SEARCH")
        for q in ("karma","yoga","gamaya"):st.write(f"Query: {q} =>",[(x[0],x[1]) for x in search(q)])
        st.markdown("#### 4. SYNTHETIC OCR EVALUATION (not real OCR)")
        rows=[]
        for r in (.05,.10,.20,.30):
            c,w=evaluate(r); rows.append({"Noise":f"{r:.0%}","CER":f"{c:.3f}","WER":f"{w:.3f}"})
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
        st.markdown("#### 5. KNOWLEDGE GRAPH")
        edges=graph_edges(); nodes=set()
        for a,b,_ in edges:nodes.update([a,b])
        st.write("Nodes:",len(nodes),"Edges:",len(edges))
        st.write("Ashtadhyayi links:",[(a,b,r) for a,b,r in edges if a=="Ashtadhyayi"])
        st.success("All five main.py modules executed successfully.")
    else:st.info("Click the button to execute the full original main.py workflow in order.")

elif page=="Digital Manuscript Catalogue":
    st.header("1. Digital Manuscript Catalogue")
    df=pd.DataFrame(CATALOGUE)
    c1,c2=st.columns(2); domain=c1.selectbox("Filter by domain",["All"]+sorted(df.domain.unique().tolist()))
    keyword=c2.text_input("Search catalogue",placeholder="Title, creator, period...")
    view=df.copy()
    if domain!="All":view=view[view.domain==domain]
    if keyword:
        view=view[view.astype(str).apply(lambda col:col.str.contains(keyword,case=False,na=False)).any(axis=1)]
    st.caption(f"{len(view)} record(s) found")
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.download_button("Download catalogue.csv",df.to_csv(index=False).encode("utf-8-sig"),"catalogue.csv","text/csv")
    st.download_button("Download catalogue.json",json.dumps(CATALOGUE,ensure_ascii=False,indent=2).encode("utf-8"),"catalogue.json","application/json")
    if st.button("Export files to outputs folder"):
        st.success(f"Exported {export_catalogue()} records to outputs/catalogue.csv and catalogue.json")

elif page=="Devanagari to IAST":
    st.header("2. Devanagari to IAST Transliteration")
    st.caption("Teaching prototype: common Devanagari characters to IAST. Limited educational mapping, not a full Vedic transliterator.")
    sample="योगश्चित्तवृत्तिनिरोधः"
    source=st.text_area("Enter Devanagari text",sample,height=120)
    if st.button("Transliterate",type="primary"):
        st.markdown("**Input**"); st.write(source); st.markdown("**Output (IAST)**"); st.code(to_iast(source))
    st.markdown("#### Corpus examples")
    for x in CORPUS[:3]:
        with st.expander(x[1]):st.write(x[2]); st.code(to_iast(x[2]))

elif page=="Search Digitized Sanskrit Text":
    st.header("3. Search Over Digitized Text")
    query=st.text_input("Search IAST / Romanized Sanskrit",placeholder="Try: karma, yoga, gamaya")
    st.caption("Searches the five original Sanskrit sample passages after transliteration and diacritic folding.")
    if query:
        hits=search(query); st.write(f"{len(hits)} result(s) found")
        for ident,source,dev,roman in hits:
            with st.container(border=True):st.markdown(f"**{ident} — {source}**"); st.write(dev); st.code(roman)
        if not hits:st.info("No match found. Try another keyword.")
    else:
        for ident,source,dev in CORPUS:
            with st.container(border=True):st.markdown(f"**{ident} — {source}**"); st.write(dev); st.caption("IAST: "+to_iast(dev))

elif page=="Synthetic OCR Evaluation":
    st.header("4. Synthetic OCR Error Evaluation")
    st.warning("This module uses synthetic noise to demonstrate CER/WER. It does not run a real OCR engine.")
    rows=[]
    for r in (.05,.10,.20,.30):
        c,w=evaluate(r); rows.append({"Noise":f"{r:.0%}","Average CER":round(c,3),"Average WER":round(w,3)})
    ocr_df=pd.DataFrame(rows); st.dataframe(ocr_df,use_container_width=True,hide_index=True)
    st.line_chart(ocr_df.set_index("Noise"))
    rate=st.slider("Noise rate for sample",0.0,0.5,0.2,0.05)
    ref=CORPUS[0][2]; hyp=noise(ref,rate)
    left,right=st.columns(2); left.markdown("**Reference text**"); left.write(ref); right.markdown("**Simulated OCR output**"); right.write(hyp)
    a,b=st.columns(2); a.metric("Character Error Rate (CER)",f"{cer(ref,hyp):.3f}"); b.metric("Word Error Rate (WER)",f"{wer(ref,hyp):.3f}")

elif page=="Knowledge Graph":
    st.header("5. Knowledge Graph")
    edges=graph_edges(); nodes=set()
    for a,b,_ in edges:nodes.update([a,b])
    c1,c2=st.columns(2); c1.metric("Nodes",len(nodes)); c2.metric("Edges",len(edges))
    title=st.selectbox("Select manuscript",[x["title"] for x in CATALOGUE])
    selected=[{"Source":a,"Relation":r,"Target":b} for a,b,r in edges if a==title]
    st.subheader(f"Outgoing links: {title}")
    if selected:st.dataframe(pd.DataFrame(selected),hide_index=True,use_container_width=True)
    else:st.info("No outgoing links found.")
    with st.expander("View all graph edges"):st.dataframe(pd.DataFrame([{"Source":a,"Relation":r,"Target":b} for a,b,r in edges]),hide_index=True,use_container_width=True)
    with st.expander("View all graph nodes"):st.write(sorted(nodes))

elif page=="SQLite Archive Database":
    st.header("6. SQLite Database and Search")
    st.write("ER diagram tables: Author, Manuscript, Digitization, Repository, User.")
    db=build_db()
    for q in ("ayurveda","sanskrit","astronomy","kautilya","xyz"):
        rows,elapsed=search_db(db,q)
        with st.expander(f"Original test query: {q} — {len(rows)} result(s)",expanded=(q=="ayurveda")):
            st.caption(f"Response time: {elapsed:.4f} sec")
            if rows:st.dataframe(pd.DataFrame(rows,columns=["Record ID","Title","Author","Language","Format","Category"]),hide_index=True,use_container_width=True)
            else:st.write("No records found.")
    st.markdown("### Interactive database search")
    term=st.text_input("Search title, author, language or category",placeholder="ayurveda / sanskrit / astronomy / kautilya")
    if term:
        rows,elapsed=search_db(db,term); st.write(f"{len(rows)} RESULT(S) FOUND | Response time: {elapsed:.4f} sec")
        if rows:st.dataframe(pd.DataFrame(rows,columns=["Record ID","Title","Author","Language","Format","Category"]),hide_index=True,use_container_width=True)
        else:st.info("No records found.")
    with st.expander("Database schema"):st.code("""Author(AuthorID, Name, Era)\nManuscript(ManuscriptID, Title, Language, Script, Category, AuthorID)\nDigitization(DigitizationID, ManuscriptID, ScanDate, Format, Resolution)\nRepository(RepositoryID, Name, Location, DigitizationID)\nUser(UserID, Name, AccessLevel)""")

elif page=="Web Search Interface":
    st.header("7. Digital Archive Web Search Interface")
    st.caption("Streamlit recreation of prototype.html: same five sample records, text search, category/language/format filters, suggested searches, result count and response-time display.")
    RECORDS=[
      {"id":"DR-001","title":"Charaka Samhita","author":"Charaka","language":"Sanskrit","format":"PDF / OCR-Text","category":"Ayurveda"},
      {"id":"DR-002","title":"Sushruta Samhita","author":"Sushruta","language":"Sanskrit","format":"Image / TIFF","category":"Ayurveda"},
      {"id":"DR-003","title":"Ashtanga Hridayam","author":"Vagbhata","language":"Sanskrit","format":"PDF","category":"Ayurveda"},
      {"id":"DR-004","title":"Surya Siddhanta","author":"Unknown","language":"Sanskrit","format":"Scanned Image","category":"Astronomy"},
      {"id":"DR-005","title":"Arthashastra (Excerpt)","author":"Kautilya","language":"Sanskrit","format":"PDF / OCR-Text","category":"Governance"}]
    q=st.text_input("Search archive",placeholder="Search: ayurveda, charaka, sanskrit...")
    f1,f2,f3=st.columns(3)
    cat=f1.selectbox("Category",["All"]+sorted({r['category'] for r in RECORDS}))
    lang=f2.selectbox("Language",["All"]+sorted({r['language'] for r in RECORDS}))
    fmt=f3.selectbox("Format",["All"]+sorted({r['format'] for r in RECORDS}))
    st.write("Try:")
    buttons=st.columns(3)
    for col,suggestion in zip(buttons,["ayurveda","sanskrit","astronomy"]):
        if col.button(suggestion):st.session_state.archive_query=suggestion
    # Suggested buttons update a persistent query field on the next rerun.
    if "archive_query" in st.session_state and st.session_state.archive_query and not q:
        q=st.session_state.archive_query
    start=time.perf_counter(); terms=q.strip().lower().split()
    hits=[]
    for r in RECORDS:
        if cat!="All" and r["category"]!=cat:continue
        if lang!="All" and r["language"]!=lang:continue
        if fmt!="All" and r["format"]!=fmt:continue
        hay=" ".join([r["title"],r["author"],r["language"],r["category"],r["format"]]).lower()
        if all(t in hay for t in terms):hits.append(r)
    elapsed=time.perf_counter()-start
    st.markdown(f"**{len(hits)} RESULT{'S' if len(hits)!=1 else ''} FOUND**  ·  Response time: {elapsed:.4f} sec")
    if hits:
        for r in hits:
            with st.container(border=True):
                st.markdown(f"### {r['title']}  `({r['id']})`")
                st.caption(f"Author: {r['author']} | Language: {r['language']} | Format: {r['format']}")
                st.markdown(f"`{r['category']}`")
    else:st.info("No records match. Try a different keyword or reset the filters.")

st.divider()
st.caption("Bharatiya Jnana Parampara — Digitization Prototype | Indian Knowledge Systems")
