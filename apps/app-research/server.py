import html
import os
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA_FILE = os.environ.get("RESEARCH_FILE", "/data/research/research.txt")

DEFAULT_RESEARCH = """ชื่อเรื่อง (ไทย): การพัฒนาระบบสืบค้นและตอบคำถามข้อมูลสารสนเทศและสถิติด้าน*****ด้วยเทคโนโลยี RAG และโมเดลภาษาขนาดใหญ่
ชื่อเรื่อง (อังกฤษ): Development of a Search and Question-Answering System for **** Information and Statistics Using RAG Technology and Large Language Models
ผู้วิจัย: นายยุทธศาสตร์ คำคนซื่อ (รหัสนักศึกษา 68130239) | หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ วิทยาลัยวิศวกรรมศาสตร์และเทคโนโลยี มหาวิทยาลัยธุรกิจบัณฑิตย์

1. บทนำและวัตถุประสงค์:
ระบบสารสนเทศและฐานข้อมูลสถิติมีผู้ใช้งานหลายระดับตั้งแต่ส่วนกลาง ภูมิภาค 1–9 จังหวัด อำเภอ จนถึง อปท. และมีการหมุนเวียนบุคลากรอย่างต่อเนื่อง ข้อมูลแบ่งเป็น 2 ลักษณะ คือ ข้อมูลไม่มีโครงสร้าง (คู่มือการใช้งาน แนวทางปฏิบัติ ระเบียบ) และข้อมูลมีโครงสร้าง (ฐานข้อมูลสถิติรายจังหวัด) การค้นหาคู่มือแบบเดิมด้วย Keyword และการวิเคราะห์สถิติที่ต้องอาศัยทักษะ SQL หรือทีม Helpdesk ทำให้เกิดความล่าช้า งานวิจัยนี้จึงมีวัตถุประสงค์ 3 ข้อ ได้แก่ (1) พัฒนาระบบต้นแบบสืบค้นและตอบคำถามด้วยภาษาธรรมชาติโดยใช้ On-premise LLM ร่วมกับ Hybrid RAG และ Text-to-SQL (2) ประเมินประสิทธิภาพเชิงเทคนิคด้านความถูกต้องของการสืบค้นเอกสาร ข้อมูลเชิงโครงสร้าง และความปลอดภัย และ (3) ศึกษาความพึงพอใจและการยอมรับเทคโนโลยีของผู้ใช้งานกลุ่มตัวอย่างแบบเจาะจงจำนวน 30 คน (เจ้าหน้าที่ นักวิเคราะห์ และ Helpdesk) โดยใช้ชุดข้อมูลสถิติจำลองและเอกสารเปิดเผยทั่วไปที่ไม่มีข้อมูลส่วนบุคคล (PII)

2. แนวคิดและสถาปัตยกรรมระบบ:
ประยุกต์ใช้ระเบียบวิธีวิจัย DSRM (Design Science Research Methodology) ร่วมกับ Agile SDLC เพื่อพัฒนาสถาปัตยกรรม Microservices 6 เลเยอร์ ได้แก่ Gateway (Nginx Rate Limit 15 req/min/IP และ SSE Buffering), Presentation (PHP Laravel 13), Application & Orchestration (FastAPI), Async Worker (Celery + Redis), Storage & Data (PostgreSQL 16 + pgvector, Qdrant Vector DB, MinIO S3) และ AI Hardware Acceleration (Ollama รองรับ Intel Arc Vulkan / NVIDIA CUDA) ระบบใช้ Semantic Pattern Matcher จำแนกเจตนาคำถามอัตโนมัติระหว่าง SQL_QUERY, DOC_SEARCH, HYBRID และ GENERAL_CHAT:
- ด้าน Document RAG: สกัดเอกสาร PDF ด้วย pdfplumber และแปลงตารางเป็น Markdown Table (Chunk 800 ตัวอักษร, Overlap 100) จากนั้นค้นคืนแบบ Hybrid 2-Stage Re-ranking โดยรวม Dense Vector (bge-m3 1,024 มิติ, Over-fetch 3×k) กับ Lexical Scoring เพื่อคัดเลือก Top-k = 3 พร้อม Citations ระบุชื่อไฟล์ เลขหน้า และคะแนนความเกี่ยวข้อง
- ด้าน Text-to-SQL และความปลอดภัย: ใช้ Dynamic Schema Linking จาก COMMENT ON COLUMN, Dynamic Few-Shot Retrieval, Self-Healing Reflection Loop แก้ SQL ผิดพลาดอัตโนมัติสูงสุด 2 รอบ และ AST Security Guardrail (sqlglot) ป้องกันคำสั่ง DDL/DML และบังคับ LIMIT 100 รวมทั้งใช้ Semantic Caching บน Redis (TTL 24 ชั่วโมง)

3. ผลการทดลองและสรุปผล:
ประเมินผลด้วย Golden Benchmark 100 คำถาม (Text-to-SQL 50 ข้อ, Document RAG 40 ข้อ, Adversarial Attacks 10 ข้อ) และการทดสอบ UAT 20 คน พบว่า:
- Text-to-SQL: Valid SQL Rate (VSR) เพิ่มจาก 72.0% (Zero-Shot) เป็น 94.0% (Few-Shot + Self-Healing), Execution Accuracy (EX) เพิ่มจาก 64.0% เป็น 92.0% และ Self-Healing Recovery Rate (SHR) กู้คืนคำสั่งผิดพลาดได้ 85.7%
- Document RAG: Hybrid 2-Stage Re-ranking เพิ่ม Precision@3 จาก 75.0% เป็น 92.5% (+17.5%), Recall@3 จาก 70.0% เป็น 90.0% (+20.0%), Faithfulness ที่ 97.5%, Table Extraction Accuracy เพิ่มจาก 55.0% เป็น 95.0% (+40.0%) และ Citation Accuracy 100.0%
- ความปลอดภัย ประสิทธิภาพ และ UAT: Attack Block Rate (ABR) ป้องกันคำสั่งโจมตีได้ 100.0% (0 ข้อผ่านเข้าฐานข้อมูล), Semantic Cache Hit ตอบสนองด้วย TTFT 12.5 ms (Total Latency 28.4 ms เร็วกว่า Cache Miss กว่า 50 เท่า), ใช้ VRAM รวม ~3.10 GB (qwen2.5:3b + bge-m3 คิดเป็น 38.7% ของ 8GB) และได้คะแนนความพึงพอใจผู้ใช้ (UAT) เฉลี่ย 4.70 (S.D. 0.46) อยู่ในระดับมากที่สุด"""


def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        tmp_path = f"{DATA_FILE}.tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_RESEARCH.strip())
        os.replace(tmp_path, DATA_FILE)


def read_research():
    ensure_data_file()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return f.read()


class ResearchHandler(BaseHTTPRequestHandler):
    def send_html(self, status_code, body):
        data = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path not in ("/research", "/research/", "/"):
            self.send_html(404, "Not Found")
            return

        content = read_research()
        word_count = len(content.split())
        escaped_content = html.escape(content).replace("\n", "<br>")
        page = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Research Summary - 68130239</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', Tahoma, sans-serif;
      background: linear-gradient(135deg, #ecfdf5 0%, #f0fdfa 55%, #eff6ff 100%);
      color: #1e293b;
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .navbar {{
      background: rgba(255, 255, 255, 0.92);
      border-bottom: 1px solid #d1fae5;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .brand {{ font-weight: 800; font-size: 1.1rem; color: #047857; }}
    .nav-links {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    .nav-links a {{ text-decoration: none; color: #475569; font-weight: 600; font-size: 0.95rem; }}
    .nav-links a:hover, .nav-links a.active {{ color: #059669; }}
    .main {{ flex: 1; padding: 36px 16px; }}
    .container {{
      max-width: 860px;
      margin: auto;
      background: #ffffff;
      padding: 40px;
      border-radius: 18px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 18px 40px rgba(5, 150, 105, 0.08);
    }}
    .header-meta {{ display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 16px; }}
    .badge {{
      display: inline-block;
      background: #d1fae5;
      color: #065f46;
      padding: 5px 14px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 700;
    }}
    .count-pill {{
      background: #f1f5f9;
      color: #475569;
      padding: 5px 12px;
      border-radius: 999px;
      font-size: 0.85rem;
      font-weight: 600;
    }}
    .count-pill.ok {{
      background: #dcfce7;
      color: #166534;
    }}
    h1 {{ color: #0f172a; margin: 0 0 8px; font-size: 1.8rem; }}
    .author {{ color: #64748b; margin: 0 0 24px; font-size: 0.95rem; }}
    .content {{
      background: #f8fafc;
      padding: 28px;
      border-radius: 14px;
      border: 1px solid #e2e8f0;
      font-size: 1.03rem;
      line-height: 1.85;
      color: #1e293b;
    }}
    .footer {{
      margin-top: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 0.92rem;
    }}
    .btn-group {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .edit-btn {{
      background: #059669;
      color: #ffffff;
      padding: 9px 18px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
    }}
    .edit-btn:hover {{ background: #047857; }}
    .admin-btn {{
      background: #f1f5f9;
      color: #334155;
      padding: 9px 16px;
      border-radius: 8px;
      text-decoration: none;
      font-weight: 600;
    }}
    .admin-btn:hover {{ background: #e2e8f0; }}
  </style>
</head>
<body>
  <nav class="navbar">
    <div class="brand">K8s Ingress Portal &bull; iam-239</div>
    <div class="nav-links">
      <a href="/">Portal</a>
      <a class="active" href="/research">Research</a>
      <a href="/api-239/Hello%2068130239">API</a>
      <a href="http://admin.iam-239.com">Admin</a>
    </div>
  </nav>

  <main class="main">
    <div class="container">
      <div class="header-meta">
        <span class="badge">Deployment: app-research</span>
        <span class="count-pill {'ok' if 300 <= word_count <= 500 else ''}">ความยาว: {word_count} คำ/กลุ่มคำ</span>
      </div>
      <h1>สรุปงานวิจัยวิชาสัมมนา</h1>
      <p class="author">โดย Yutthasatr Khumkhonsue (รหัสนักศึกษา 68130239)</p>
      <div class="content">{escaped_content}</div>
      <div class="footer">
        <span style="color:#64748b;">Storage: PersistentVolumeClaim (research-pvc-239)</span>
        <div class="btn-group">
          <a class="admin-btn" href="http://admin.iam-239.com">หน้าเมนู Admin</a>
          <a class="edit-btn" href="http://admin.iam-239.com/research">แก้ไขบทความ Research &rarr;</a>
        </div>
      </div>
    </div>
  </main>
</body>
</html>"""
        self.send_html(200, page)


if __name__ == "__main__":
    ensure_data_file()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), ResearchHandler)
    print("app-research listening on port 8080...", flush=True)
    server.serve_forever()
