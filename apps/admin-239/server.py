import html
import json
import os
import shutil
import urllib.parse
from email.parser import BytesParser
from email.policy import default
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTAL_DIR = os.environ.get("PORTAL_DIR", "/data/portal")
RESEARCH_FILE = os.environ.get("RESEARCH_FILE", "/data/research/research.txt")
DEFAULT_AVATAR = os.environ.get("DEFAULT_AVATAR", "/app/avatar.svg")
PROFILE_FILE = os.path.join(PORTAL_DIR, "profile.json")

MAX_BODY_BYTES = 10 * 1024 * 1024
MAX_AVATAR_BYTES = 8 * 1024 * 1024

ALLOWED_AVATARS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
}

DEFAULT_PROFILE = {
    "full_name": "Yutthasatr Khumkhonsue",
    "student_id": "68130239",
    "title": "นักศึกษาปริญญาโท สาขาวิชาวิศวกรรมคอมพิวเตอร์",
    "bio": "วิทยาลัยวิศวกรรมศาสตร์และเทคโนโลยี มหาวิทยาลัยธุรกิจบัณฑิตย์ | Kubernetes Multi-Service & Ingress Project",
    "avatar_file": "avatar.svg",
    "avatar_mime": "image/svg+xml",
}

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


def atomic_write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp.{os.getpid()}"
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.replace(tmp_path, path)


def atomic_write_text(path, text):
    atomic_write_bytes(path, text.encode("utf-8"))


def atomic_write_json(path, payload):
    atomic_write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def ensure_portal_data():
    os.makedirs(PORTAL_DIR, exist_ok=True)
    if not os.path.exists(PROFILE_FILE):
        atomic_write_json(PROFILE_FILE, DEFAULT_PROFILE)
    default_avatar_dst = os.path.join(PORTAL_DIR, "avatar.svg")
    if not os.path.exists(default_avatar_dst) and os.path.exists(DEFAULT_AVATAR):
        tmp_path = f"{default_avatar_dst}.tmp.{os.getpid()}"
        shutil.copyfile(DEFAULT_AVATAR, tmp_path)
        os.replace(tmp_path, default_avatar_dst)


def load_profile():
    ensure_portal_data()
    profile = dict(DEFAULT_PROFILE)
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            stored = json.load(f)
        if isinstance(stored, dict):
            for key in DEFAULT_PROFILE:
                val = stored.get(key)
                if isinstance(val, str) and val.strip():
                    profile[key] = val.strip()
    except (OSError, json.JSONDecodeError):
        pass
    return profile


def resolve_avatar_path(profile):
    avatar_name = os.path.basename(profile.get("avatar_file", "avatar.svg"))
    candidate = os.path.join(PORTAL_DIR, avatar_name)
    if os.path.isfile(candidate):
        return candidate, profile.get("avatar_mime", "image/svg+xml")
    if os.path.isfile(DEFAULT_AVATAR):
        return DEFAULT_AVATAR, "image/svg+xml"
    return None, None


def ensure_research_file():
    os.makedirs(os.path.dirname(RESEARCH_FILE), exist_ok=True)
    if not os.path.exists(RESEARCH_FILE):
        atomic_write_text(RESEARCH_FILE, DEFAULT_RESEARCH.strip())


def read_research():
    ensure_research_file()
    with open(RESEARCH_FILE, "r", encoding="utf-8") as f:
        return f.read()


def cleanup_old_avatars(keep_filename):
    for name in os.listdir(PORTAL_DIR):
        if name.startswith("avatar.") and name != keep_filename:
            try:
                os.remove(os.path.join(PORTAL_DIR, name))
            except OSError:
                pass


def render_layout(title, active_nav, body_html):
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{html.escape(title)}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', Tahoma, sans-serif;
      background: linear-gradient(135deg, #f5f3ff 0%, #eff6ff 55%, #fef3c7 100%);
      color: #1e293b;
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .navbar {{
      background: rgba(255, 255, 255, 0.94);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid #ddd6fe;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .brand {{ font-weight: 800; font-size: 1.05rem; color: #6d28d9; display: flex; align-items: center; gap: 10px; }}
    .admin-pill {{ background: #fef3c7; color: #b45309; border: 1px solid #fcd34d; padding: 3px 10px; border-radius: 999px; font-size: 0.75rem; }}
    .nav-links {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    .nav-links a {{ text-decoration: none; color: #475569; font-weight: 600; font-size: 0.95rem; }}
    .nav-links a:hover, .nav-links a.active {{ color: #6d28d9; }}
    .main {{ flex: 1; padding: 36px 18px; display: flex; justify-content: center; align-items: flex-start; }}
    .container {{
      max-width: 900px;
      width: 100%;
      background: #ffffff;
      padding: 34px;
      border-radius: 20px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 20px 45px rgba(109, 40, 217, 0.09);
    }}
    h1 {{ color: #5b21b6; margin: 0 0 8px; font-size: 1.65rem; }}
    .sub {{ color: #64748b; margin: 0 0 24px; font-size: 0.95rem; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 20px;
    }}
    .choice-card {{
      background: #f8fafc;
      border: 1.5px solid #e2e8f0;
      border-radius: 16px;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .choice-card h2 {{ margin: 0; font-size: 1.2rem; color: #0f172a; }}
    .choice-card p {{ margin: 0; color: #475569; font-size: 0.92rem; line-height: 1.55; }}
    .preview-row {{
      display: flex;
      align-items: center;
      gap: 14px;
      background: #ffffff;
      padding: 12px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
    }}
    .mini-avatar {{
      width: 56px;
      height: 56px;
      border-radius: 50%;
      object-fit: cover;
      border: 2px solid #c7d2fe;
      background: #f1f5f9;
      flex-shrink: 0;
    }}
    .stat-box {{
      background: #ffffff;
      padding: 14px;
      border-radius: 12px;
      border: 1px solid #e2e8f0;
      font-size: 0.92rem;
      color: #334155;
    }}
    .btn {{
      display: inline-block;
      text-align: center;
      text-decoration: none;
      background: linear-gradient(135deg, #7c3aed, #6d28d9);
      color: #ffffff;
      border: none;
      padding: 12px 22px;
      border-radius: 10px;
      font-size: 0.98rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 6px 16px rgba(124, 58, 237, 0.24);
    }}
    .btn:hover {{ opacity: 0.94; }}
    .btn-teal {{
      background: linear-gradient(135deg, #059669, #047857);
      box-shadow: 0 6px 16px rgba(5, 150, 105, 0.24);
    }}
    .btn-secondary {{
      display: inline-block;
      text-decoration: none;
      background: #f1f5f9;
      color: #334155;
      padding: 11px 18px;
      border-radius: 10px;
      font-size: 0.95rem;
      font-weight: 600;
    }}
    .btn-secondary:hover {{ background: #e2e8f0; }}
    .alert {{
      background: #ecfdf5;
      color: #065f46;
      border: 1px solid #6ee7b7;
      padding: 12px 16px;
      border-radius: 10px;
      margin-bottom: 18px;
      font-weight: 600;
    }}
    .alert a {{ color: #047857; margin-left: 8px; }}
    .form-group {{ margin-bottom: 16px; }}
    label {{ display: block; font-weight: 700; color: #334155; margin-bottom: 6px; font-size: 0.94rem; }}
    input[type="text"], textarea {{
      width: 100%;
      padding: 12px 14px;
      border-radius: 10px;
      border: 1.5px solid #cbd5e1;
      background: #f8fafc;
      color: #0f172a;
      font-family: inherit;
      font-size: 0.98rem;
      outline: none;
    }}
    input[type="text"]:focus, textarea:focus {{ border-color: #7c3aed; background: #ffffff; }}
    textarea {{ height: 340px; line-height: 1.7; resize: vertical; }}
    .avatar-editor {{
      display: flex;
      gap: 18px;
      align-items: center;
      flex-wrap: wrap;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 16px;
      border-radius: 12px;
    }}
    .preview-avatar {{
      width: 96px;
      height: 96px;
      border-radius: 50%;
      object-fit: cover;
      border: 3px solid #ffffff;
      box-shadow: 0 6px 16px rgba(15, 23, 42, 0.14);
      background: #ffffff;
    }}
    .checkbox-row {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 8px;
      font-size: 0.9rem;
      color: #475569;
    }}
    .toolbar {{
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .counter {{ font-size: 0.92rem; color: #475569; background: #f1f5f9; padding: 8px 14px; border-radius: 8px; }}
    .counter.ok {{ background: #dcfce7; color: #166534; font-weight: 600; }}
  </style>
</head>
<body>
  <nav class="navbar">
    <div class="brand">Admin Panel (admin-239) <span class="admin-pill">ADMIN MODE</span></div>
    <div class="nav-links">
      <a class="{'active' if active_nav == 'home' else ''}" href="/">เมนูหลัก Admin</a>
      <a class="{'active' if active_nav == 'portal' else ''}" href="/portal">แก้ไข Portal</a>
      <a class="{'active' if active_nav == 'research' else ''}" href="/research">แก้ไข Research</a>
      <a href="http://www.iam-239.com/">ดูหน้า Portal</a>
      <a href="http://www.iam-239.com/research">ดูหน้า Research</a>
      <a href="http://www.iam-239.com/api-239/Hello%2068130239">API</a>
    </div>
  </nav>
  <main class="main">
    <div class="container">
      {body_html}
    </div>
  </main>
</body>
</html>"""


class AdminHandler(BaseHTTPRequestHandler):
    def send_bytes(self, status_code, content_type, data):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def redirect(self, location):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        path = parsed.path

        if path == "/avatar":
            profile = load_profile()
            avatar_path, mime = resolve_avatar_path(profile)
            if not avatar_path:
                self.send_bytes(404, "text/plain; charset=utf-8", b"Not Found")
                return
            with open(avatar_path, "rb") as f:
                self.send_bytes(200, mime, f.read())
            return

        if path == "/":
            profile = load_profile()
            avatar_path, _ = resolve_avatar_path(profile)
            mtime = int(os.path.getmtime(avatar_path)) if avatar_path and os.path.exists(avatar_path) else 0
            research_words = len(read_research().split())
            body = f"""
      <h1>ศูนย์จัดการข้อมูลระบบ (admin.iam-239.com)</h1>
      <p class="sub">Deployment: <strong>admin-239</strong> &bull; เลือกบริการที่ต้องการแก้ไขข้อมูลและบันทึกลง Persistent Storage (PVC)</p>
      <div class="grid">
        <div class="choice-card">
          <h2>1. ข้อมูลหน้า Portal (portal-239)</h2>
          <p>แก้ไขชื่อ-นามสกุล, รหัสนักศึกษา, ตำแหน่ง/สังกัด และอัปโหลดเปลี่ยนรูปโปรไฟล์ที่แสดงบน <strong>www.iam-239.com</strong></p>
          <div class="preview-row">
            <img class="mini-avatar" src="/avatar?t={mtime}" alt="Avatar" />
            <div>
              <strong>{html.escape(profile["full_name"])}</strong><br />
              <span style="color:#64748b;font-size:0.88rem;">ID: {html.escape(profile["student_id"])}</span>
            </div>
          </div>
          <a class="btn" href="/portal">เลือกแก้ไขข้อมูล Portal &rarr;</a>
        </div>

        <div class="choice-card">
          <h2>2. บทสรุปงานวิจัย (app-research)</h2>
          <p>แก้ไขบทสรุปงานวิจัยวิชาสัมมนาความยาว 300 - 500 คำ ที่แสดงบน <strong>www.iam-239.com/research</strong></p>
          <div class="stat-box">
            สถานะปัจจุบัน: <strong>{research_words} คำ/กลุ่มคำ</strong><br />
            Storage: <strong>research-pvc-239</strong>
          </div>
          <a class="btn btn-teal" href="/research">เลือกแก้ไขข้อมูล Research &rarr;</a>
        </div>
      </div>"""
            self.send_bytes(200, "text/html; charset=utf-8", render_layout("Admin Dashboard - admin-239", "home", body).encode("utf-8"))
            return

        if path in ("/portal", "/portal/"):
            profile = load_profile()
            avatar_path, _ = resolve_avatar_path(profile)
            mtime = int(os.path.getmtime(avatar_path)) if avatar_path and os.path.exists(avatar_path) else 0
            saved_banner = (
                '<div class="alert">บันทึกข้อมูล Portal ลง PVC เรียบร้อยแล้ว! '
                '<a href="http://www.iam-239.com/" target="_blank">เปิดดูหน้า www.iam-239.com &rarr;</a></div>'
                if query.get("saved") == ["1"]
                else ""
            )
            body = f"""
      <h1>แก้ไขข้อมูลหน้า Portal (portal-239)</h1>
      <p class="sub">บันทึกลง <strong>portal-pvc-239</strong> &bull; แสดงผลที่ <a href="http://www.iam-239.com/" target="_blank">http://www.iam-239.com/</a></p>
      {saved_banner}
      <form method="POST" action="/portal" enctype="multipart/form-data">
        <div class="form-group">
          <label for="full_name">ชื่อ-นามสกุล</label>
          <input id="full_name" type="text" name="full_name" value="{html.escape(profile['full_name'])}" required />
        </div>
        <div class="form-group">
          <label for="student_id">รหัสนักศึกษา</label>
          <input id="student_id" type="text" name="student_id" value="{html.escape(profile['student_id'])}" required />
        </div>
        <div class="form-group">
          <label for="title">หลักสูตร / สาขาวิชา</label>
          <input id="title" type="text" name="title" value="{html.escape(profile['title'])}" required />
        </div>
        <div class="form-group">
          <label for="bio">สังกัด / คำอธิบาย</label>
          <input id="bio" type="text" name="bio" value="{html.escape(profile['bio'])}" required />
        </div>
        <div class="form-group">
          <label>รูปโปรไฟล์ (PNG, JPG, WEBP, GIF, SVG สูงสุด 8MB)</label>
          <div class="avatar-editor">
            <img class="preview-avatar" src="/avatar?t={mtime}" alt="Current Avatar" />
            <div>
              <input type="file" name="avatar" accept="image/png,image/jpeg,image/webp,image/gif,image/svg+xml" />
              <label class="checkbox-row">
                <input type="checkbox" name="reset_avatar" value="1" /> รีเซ็ตกลับเป็นรูป Vector เริ่มต้น (avatar.svg)
              </label>
            </div>
          </div>
        </div>
        <div class="toolbar">
          <a class="btn-secondary" href="/">&larr; กลับเมนูหลัก Admin</a>
          <button class="btn" type="submit">บันทึกข้อมูล Portal (Save to PVC)</button>
        </div>
      </form>"""
            self.send_bytes(200, "text/html; charset=utf-8", render_layout("Admin - แก้ไข Portal", "portal", body).encode("utf-8"))
            return

        if path in ("/research", "/research/", "/edit", "/edit/"):
            content = html.escape(read_research())
            saved_banner = (
                '<div class="alert">บันทึกข้อมูลสรุปงานวิจัยลง PVC เรียบร้อยแล้ว! '
                '<a href="http://www.iam-239.com/research" target="_blank">เปิดดูหน้า www.iam-239.com/research &rarr;</a></div>'
                if query.get("saved") == ["1"]
                else ""
            )
            body = f"""
      <h1>แก้ไขสรุปงานวิจัยวิชาสัมมนา (app-research)</h1>
      <p class="sub">บันทึกลง <strong>research-pvc-239</strong> &bull; แสดงผลที่ <a href="http://www.iam-239.com/research" target="_blank">http://www.iam-239.com/research</a></p>
      {saved_banner}
      <form method="POST" action="/research">
        <textarea id="editor" name="content" required>{content}</textarea>
        <div class="toolbar">
          <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
            <a class="btn-secondary" href="/">&larr; กลับเมนูหลัก Admin</a>
            <div id="counter" class="counter">กำลังนับคำ...</div>
          </div>
          <button class="btn btn-teal" type="submit">บันทึกข้อมูล Research (Save to PVC)</button>
        </div>
      </form>
      <script>
        const editor = document.getElementById('editor');
        const counter = document.getElementById('counter');
        function updateCount() {{
          const text = editor.value.trim();
          const words = text ? text.split(/\\s+/).length : 0;
          const chars = text.length;
          counter.textContent = `จำนวนคำ (Whitespace): ${{words}} คำ | ตัวอักษร: ${{chars}} ตัว`;
          counter.className = (words >= 300 && words <= 500) ? 'counter ok' : 'counter';
        }}
        editor.addEventListener('input', updateCount);
        updateCount();
      </script>"""
            self.send_bytes(200, "text/html; charset=utf-8", render_layout("Admin - แก้ไข Research", "research", body).encode("utf-8"))
            return

        self.send_bytes(404, "text/plain; charset=utf-8", b"Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        if length < 0 or length > MAX_BODY_BYTES:
            self.send_bytes(413, "text/plain; charset=utf-8", b"Payload Too Large")
            return

        raw = self.rfile.read(length)
        content_type = self.headers.get("Content-Type", "")

        if path in ("/portal", "/portal/"):
            fields = {}
            avatar_upload = None

            if content_type.lower().startswith("multipart/form-data"):
                header_bytes = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n".encode("utf-8")
                msg = BytesParser(policy=default).parsebytes(header_bytes + raw)
                for part in msg.iter_parts():
                    name = part.get_param("name", header="content-disposition")
                    if not name:
                        continue
                    filename = part.get_filename()
                    payload = part.get_payload(decode=True) or b""
                    if filename is not None:
                        if filename.strip() and payload:
                            avatar_upload = (filename.strip(), payload)
                    else:
                        fields[name] = payload.decode("utf-8", errors="replace").strip()
            else:
                form = urllib.parse.parse_qs(raw.decode("utf-8", errors="replace"))
                for key, values in form.items():
                    fields[key] = values[0].strip() if values else ""

            profile = load_profile()
            for key in ("full_name", "student_id", "title", "bio"):
                val = fields.get(key, "").strip()
                if val:
                    profile[key] = val

            if fields.get("reset_avatar") == "1":
                dst = os.path.join(PORTAL_DIR, "avatar.svg")
                if os.path.exists(DEFAULT_AVATAR):
                    with open(DEFAULT_AVATAR, "rb") as f:
                        atomic_write_bytes(dst, f.read())
                cleanup_old_avatars("avatar.svg")
                profile["avatar_file"] = "avatar.svg"
                profile["avatar_mime"] = "image/svg+xml"
            elif avatar_upload is not None:
                orig_name, payload = avatar_upload
                if len(payload) > MAX_AVATAR_BYTES:
                    self.send_bytes(400, "text/plain; charset=utf-8", b"Avatar image exceeds 8MB limit")
                    return
                ext = os.path.splitext(os.path.basename(orig_name))[1].lower()
                if ext not in ALLOWED_AVATARS:
                    self.send_bytes(400, "text/plain; charset=utf-8", b"Unsupported image type")
                    return
                new_filename = f"avatar{ext}"
                atomic_write_bytes(os.path.join(PORTAL_DIR, new_filename), payload)
                cleanup_old_avatars(new_filename)
                profile["avatar_file"] = new_filename
                profile["avatar_mime"] = ALLOWED_AVATARS[ext]

            atomic_write_json(PROFILE_FILE, profile)
            self.redirect("/portal?saved=1")
            return

        if path in ("/research", "/research/", "/edit", "/edit/"):
            form = urllib.parse.parse_qs(raw.decode("utf-8", errors="replace"))
            new_content = form.get("content", [""])[0].strip()
            if new_content:
                ensure_research_file()
                atomic_write_text(RESEARCH_FILE, new_content)
            self.redirect("/research?saved=1")
            return

        self.send_bytes(404, "text/plain; charset=utf-8", b"Not Found")


if __name__ == "__main__":
    ensure_portal_data()
    ensure_research_file()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), AdminHandler)
    print("admin-239 listening on port 8080...", flush=True)
    server.serve_forever()
