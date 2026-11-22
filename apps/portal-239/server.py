import html
import json
import os
import shutil
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTAL_DIR = os.environ.get("PORTAL_DIR", "/data/portal")
DEFAULT_AVATAR = os.environ.get("DEFAULT_AVATAR", "/app/avatar.svg")
PROFILE_FILE = os.path.join(PORTAL_DIR, "profile.json")

DEFAULT_PROFILE = {
    "full_name": "Yutthasatr Khumkhonsue",
    "student_id": "68130239",
    "title": "นักศึกษาปริญญาโท สาขาวิชาวิศวกรรมคอมพิวเตอร์",
    "bio": "วิทยาลัยวิศวกรรมศาสตร์และเทคโนโลยี มหาวิทยาลัยธุรกิจบัณฑิตย์ | Kubernetes Multi-Service & Ingress Project",
    "avatar_file": "avatar.svg",
    "avatar_mime": "image/svg+xml",
}


def atomic_write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp.{os.getpid()}"
    with open(tmp_path, "wb") as f:
        f.write(data)
    os.replace(tmp_path, path)


def atomic_write_json(path, payload):
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    atomic_write_bytes(path, data)


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


class PortalHandler(BaseHTTPRequestHandler):
    def send_bytes(self, status_code, content_type, data):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/avatar", "/about/avatar.svg"):
            profile = load_profile()
            avatar_path, mime = resolve_avatar_path(profile)
            if not avatar_path:
                self.send_bytes(404, "text/plain; charset=utf-8", b"Avatar Not Found")
                return
            with open(avatar_path, "rb") as f:
                self.send_bytes(200, mime, f.read())
            return

        if path in ("/", "/about", "/about/", "/index.html"):
            profile = load_profile()
            avatar_path, _ = resolve_avatar_path(profile)
            mtime = int(os.path.getmtime(avatar_path)) if avatar_path and os.path.exists(avatar_path) else 0

            safe_name = html.escape(profile["full_name"])
            safe_id = html.escape(profile["student_id"])
            safe_title = html.escape(profile["title"])
            safe_bio = html.escape(profile["bio"])

            page = f"""<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Portal - {safe_name} ({safe_id})</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Segoe UI', Tahoma, sans-serif;
      background: linear-gradient(135deg, #eff6ff 0%, #e0e7ff 50%, #f0fdfa 100%);
      color: #1e293b;
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }}
    .navbar {{
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid #e2e8f0;
      padding: 14px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    .brand {{ font-weight: 800; font-size: 1.1rem; color: #1d4ed8; letter-spacing: 0.3px; }}
    .nav-links {{ display: flex; gap: 18px; flex-wrap: wrap; }}
    .nav-links a {{ text-decoration: none; color: #475569; font-weight: 600; font-size: 0.95rem; }}
    .nav-links a:hover, .nav-links a.active {{ color: #2563eb; }}
    .main {{
      flex: 1;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 36px 20px;
    }}
    .portal-wrap {{
      max-width: 920px;
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 28px;
    }}
    .profile-card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 24px;
      overflow: hidden;
      box-shadow: 0 20px 45px rgba(37, 99, 235, 0.12);
    }}
    .banner {{
      height: 124px;
      background: linear-gradient(135deg, #0284c7 0%, #2563eb 55%, #4f46e5 100%);
      display: flex;
      justify-content: flex-end;
      align-items: flex-start;
      padding: 16px 22px;
    }}
    .banner-tag {{
      background: rgba(255, 255, 255, 0.2);
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.35);
      padding: 5px 14px;
      border-radius: 999px;
      font-size: 0.8rem;
      font-weight: 700;
    }}
    .profile-content {{
      padding: 0 32px 32px;
      display: flex;
      gap: 28px;
      align-items: center;
      flex-wrap: wrap;
    }}
    .avatar-wrap {{
      margin-top: -68px;
      flex-shrink: 0;
    }}
    .avatar {{
      width: 160px;
      height: 160px;
      border-radius: 50%;
      object-fit: cover;
      border: 5px solid #ffffff;
      box-shadow: 0 10px 26px rgba(15, 23, 42, 0.16);
      background: #f1f5f9;
      display: block;
    }}
    .details {{
      flex: 1;
      min-width: 240px;
      padding-top: 16px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 1.85rem; color: #0f172a; }}
    .id-badge {{
      display: inline-block;
      background: #dbeafe;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
      padding: 5px 16px;
      border-radius: 999px;
      font-weight: 800;
      font-size: 0.98rem;
      letter-spacing: 0.6px;
      margin-bottom: 12px;
    }}
    .role-title {{ font-weight: 700; color: #334155; margin: 0 0 6px; font-size: 1rem; }}
    .bio {{ color: #64748b; margin: 0 0 14px; font-size: 0.94rem; line-height: 1.6; }}
    .meta-row {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      font-size: 0.82rem;
      color: #475569;
    }}
    .meta-chip {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      padding: 4px 10px;
      border-radius: 8px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      padding: 20px;
      text-decoration: none;
      color: inherit;
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
      transition: transform 0.2s, box-shadow 0.2s;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .card:hover {{
      transform: translateY(-3px);
      box-shadow: 0 14px 30px rgba(37, 99, 235, 0.12);
    }}
    .badge {{
      display: inline-block;
      width: fit-content;
      padding: 4px 10px;
      border-radius: 8px;
      font-size: 0.75rem;
      font-weight: 700;
    }}
    .b-blue {{ background: #dbeafe; color: #1d4ed8; }}
    .b-teal {{ background: #d1fae5; color: #047857; }}
    .b-pink {{ background: #fce7f3; color: #be185d; }}
    .b-violet {{ background: #ede9fe; color: #6d28d9; }}
    .card h2 {{ margin: 0; font-size: 1.05rem; color: #0f172a; }}
    .card p {{ margin: 0; color: #64748b; font-size: 0.86rem; line-height: 1.45; }}
    .card .url {{ margin-top: auto; padding-top: 6px; font-size: 0.82rem; font-weight: 700; color: #2563eb; }}
  </style>
</head>
<body>
  <nav class="navbar">
    <div class="brand">K8s Ingress Portal &bull; iam-239</div>
    <div class="nav-links">
      <a class="active" href="/">Portal</a>
      <a href="/research">Research</a>
      <a href="/api-239/Hello%2068130239">API</a>
      <a href="http://admin.iam-239.com">Admin</a>
    </div>
  </nav>

  <main class="main">
    <div class="portal-wrap">
      <section class="profile-card">
        <div class="banner">
          <span class="banner-tag">Kubernetes 3-Node Cluster &bull; www.iam-239.com</span>
        </div>
        <div class="profile-content">
          <div class="avatar-wrap">
            <img class="avatar" src="/avatar?t={mtime}" alt="{safe_name}" />
          </div>
          <div class="details">
            <h1>{safe_name}</h1>
            <div class="id-badge">Student ID: {safe_id}</div>
            <p class="role-title">{safe_title}</p>
            <p class="bio">{safe_bio}</p>
            <div class="meta-row">
              <span class="meta-chip">Deployment: <strong>portal-239</strong></span>
              <span class="meta-chip">Host: <strong>www.iam-239.com</strong></span>
              <span class="meta-chip">Storage: <strong>portal-pvc-239</strong></span>
            </div>
          </div>
        </div>
      </section>

      <section class="grid">
        <a class="card" href="/">
          <span class="badge b-blue">Deployment: portal-239</span>
          <h2>1. ข้อมูลนักศึกษา (Portal)</h2>
          <p>แสดงรูปโปรไฟล์ ชื่อ-นามสกุล และรหัสนักศึกษาจาก PVC</p>
          <div class="url">www.iam-239.com/ &rarr;</div>
        </a>

        <a class="card" href="/research">
          <span class="badge b-teal">Deployment: app-research</span>
          <h2>2. สรุปงานวิจัย (/research)</h2>
          <p>สรุปงานวิจัยวิชาสัมมนา 300 - 500 คำ (อ่านจาก PVC)</p>
          <div class="url">www.iam-239.com/research &rarr;</div>
        </a>

        <a class="card" href="/api-239/Hello%2068130239">
          <span class="badge b-pink">Deployment: api-239</span>
          <h2>3. API ข้อความ (/api-239/...)</h2>
          <p>นำข้อความจาก URL มาแสดงขนาดใหญ่กลางหน้าจอ</p>
          <div class="url">www.iam-239.com/api-239/... &rarr;</div>
        </a>

        <a class="card" href="http://admin.iam-239.com">
          <span class="badge b-violet">Deployment: admin-239</span>
          <h2>4. จัดการข้อมูล (Admin)</h2>
          <p>เลือกแก้ไขข้อมูล Portal (รูป/ข้อความ) และ Research</p>
          <div class="url">admin.iam-239.com &rarr;</div>
        </a>
      </section>
    </div>
  </main>
</body>
</html>"""
            self.send_bytes(200, "text/html; charset=utf-8", page.encode("utf-8"))
            return

        self.send_bytes(404, "text/plain; charset=utf-8", b"Not Found")


if __name__ == "__main__":
    ensure_portal_data()
    server = ThreadingHTTPServer(("0.0.0.0", 8080), PortalHandler)
    print("portal-239 listening on port 8080...", flush=True)
    server.serve_forever()
