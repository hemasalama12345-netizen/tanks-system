import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import text

# ================================================================
# QR Code Generator — يستخدم qrcode library إذا متوفرة
# ================================================================
import io as _io, base64 as _b64
from PIL import Image as _Img, ImageDraw as _Draw

# محاولة استخدام مكتبة qrcode الحقيقية
_QRCODE_LIB = None
try:
    import qrcode as _qrcode_lib
    import qrcode.constants as _qrc
    _QRCODE_LIB = _qrcode_lib
except ImportError:
    pass

def make_qr_b64(text, color=(0,0,0), module_size=10, quiet=4):
    """توليد QR Code — qrcode library أولاً ثم API"""
    # 1. qrcode library (Streamlit Cloud بعد install)
    if _QRCODE_LIB is not None:
        try:
            qr = _QRCODE_LIB.QRCode(
                version=None,
                error_correction=_qrc.ERROR_CORRECT_M,
                box_size=module_size,
                border=quiet,
            )
            qr.add_data(text.encode('utf-8') if isinstance(text, str) else text)
            qr.make(fit=True)
            r2,g2,b2 = color if isinstance(color,tuple) else (0,0,0)
            img = qr.make_image(fill_color=(r2,g2,b2), back_color=(255,255,255))
            buf = _io.BytesIO()
            img.save(buf, format='PNG')
            result = _b64.b64encode(buf.getvalue()).decode()
            if len(result) > 500:  # QR حقيقي
                return result
        except Exception:
            pass
    # 2. API fallback
    return _make_qr_fallback(text, color, module_size, quiet)

def _make_qr_fallback(text, color=(0,0,0), module_size=10, quiet=4):
    """QR عبر api.qrserver.com — يعمل على Streamlit Cloud دائماً"""
    import urllib.parse, urllib.request
    try:
        encoded = urllib.parse.quote(text)
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded}&ecc=M&margin=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return _b64.b64encode(resp.read()).decode()
    except Exception:
        # fallback أوفلاين
        size = module_size * 25 + quiet * 2 * module_size
        img = _Img.new('RGB', (size, size), (255,255,255))
        draw = _Draw.Draw(img)
        draw.rectangle([0,0,size-1,size-1], outline=(0,0,0), width=3)
        buf = _io.BytesIO()
        img.save(buf, format='PNG')
        return _b64.b64encode(buf.getvalue()).decode()

def _gf_mul(x, y, _EXP=[None], _LOG=[None]):
    if _EXP[0] is None:
        exp = []
        result = 1
        for _ in range(255):
            exp.append(result)
            result <<= 1
            if result >= 256: result ^= 285
        _EXP[0] = exp + exp
        log = [0]*256
        for i in range(255): log[exp[i]] = i
        _LOG[0] = log
    if x==0 or y==0: return 0
    return _EXP[0][(_LOG[0][x]+_LOG[0][y])%255]

def _rs_encode(data, n_ec):
    def _poly_mul(p,q):
        r=[0]*(len(p)+len(q)-1)
        for j,qj in enumerate(q):
            for i,pi in enumerate(p): r[i+j]^=_gf_mul(pi,qj)
        return r
    exp_table=[]
    r2=1
    for _ in range(255):
        exp_table.append(r2); r2<<=1
        if r2>=256: r2^=285
    exp_table+=exp_table
    g=[1]
    for i in range(n_ec):
        g2=[0]*(len(g)+1)
        alpha_i=exp_table[i]
        for k,gk in enumerate(g): g2[k]^=gk
        for k,gk in enumerate(g): g2[k+1]^=_gf_mul(gk,alpha_i)
        g=g2
    msg=list(data)+[0]*n_ec
    for i in range(len(data)):
        c=msg[i]
        if c:
            for j,gj in enumerate(g): msg[i+j]^=_gf_mul(gj,c)
    return msg[len(data):]

def _make_qr_b64_old(text, color=(30,58,138), module_size=8, quiet=4):
    """النسخة القديمة — غير مستخدمة"""
    raw = text.encode('latin-1', errors='replace')
    n = len(raw)
    # version selection (Byte mode, Error Level L)
    caps = [(1,19,7,7),(2,34,10,16),(3,55,15,19),(4,80,20,25),(5,108,26,31),
            (6,136,18,36),(7,156,20,40),(8,194,24,48),(9,232,30,60),(10,274,18,70)]
    ver,size_,ec,dc = next(((v,17+4*v,e,d) for v,cap,e,d in caps if n<=cap), (10,57,18,70))
    size = 17+4*ver
    M=[[None]*size for _ in range(size)]
    def sf(r,c,v):
        if 0<=r<size and 0<=c<size: M[r][c]=v
    def finder(r,c):
        for i in range(-1,8):
            for j in range(-1,8):
                if not(0<=r+i<size and 0<=c+j<size): continue
                if i in(-1,7) or j in(-1,7): M[r+i][c+j]=0
                elif i in(0,6) or j in(0,6): M[r+i][c+j]=1
                elif 2<=i<=4 and 2<=j<=4: M[r+i][c+j]=1
                else: M[r+i][c+j]=0
    finder(0,0); finder(0,size-7); finder(size-7,0)
    for i in range(8,size-8):
        M[6][i]=i%2==0; M[i][6]=i%2==0
    for i in range(9):
        if M[8][i] is None: M[8][i]=0
        if M[i][8] is None: M[i][8]=0
    for i in range(size-8,size):
        if M[8][i] is None: M[8][i]=0
        if M[i][8] is None: M[i][8]=0
    M[size-8][8]=1
    # alignment
    alc={2:[6,18],3:[6,22],4:[6,26],5:[6,30],6:[6,34],7:[6,22,38],8:[6,24,42],9:[6,26,46],10:[6,28,50]}
    for ar in alc.get(ver,[]):
        for ac in alc.get(ver,[]):
            if M[ar][ac] is not None: continue
            for dr in range(-2,3):
                for dc2 in range(-2,3):
                    rr,cc=ar+dr,ac+dc2
                    if 0<=rr<size and 0<=cc<size:
                        if abs(dr)==2 or abs(dc2)==2: M[rr][cc]=1
                        elif dr==0 and dc2==0: M[rr][cc]=1
                        else: M[rr][cc]=0
    # encode
    dn=min(n,dc)
    bits=[0,1,0,0]
    for i in range(7,-1,-1): bits.append((dn>>i)&1)
    for byte in raw[:dc]:
        for i in range(7,-1,-1): bits.append((byte>>i)&1)
    bits+=[0,0,0,0]
    while len(bits)%8: bits.append(0)
    pad=[0xEC,0x11]; pi=0; total=dc*8
    while len(bits)<total:
        for b in range(7,-1,-1): bits.append((pad[pi%2]>>b)&1)
        pi+=1
    dc_b=[]
    for i in range(0,total,8):
        v=0
        for b in bits[i:i+8]: v=(v<<1)|b
        dc_b.append(v)
    ec_b=_rs_encode(bytes(dc_b),ec)
    all_bytes=dc_b+list(ec_b)
    all_bits=[]
    for byte in all_bytes:
        for i in range(7,-1,-1): all_bits.append((byte>>i)&1)
    bi=0; col=size-1; up=True
    while col>=0:
        if col==6: col-=1
        rows=range(size-1,-1,-1) if up else range(size)
        for row in rows:
            for co in [0,-1]:
                c=col+co
                if 0<=c<size and M[row][c] is None:
                    b=all_bits[bi] if bi<len(all_bits) else 0
                    M[row][c]=b^(1 if (row+c)%2==0 else 0)
                    bi+=1
        col-=2; up=not up
    for r in range(size):
        for c in range(size):
            if M[r][c] is None: M[r][c]=0
    # render
    ns=(size+2*quiet)*module_size
    img=_Img.new('RGB',(ns,ns),(255,255,255))
    draw=_Draw.Draw(img)
    for r in range(size):
        for c in range(size):
            if M[r][c]:
                x0=(c+quiet)*module_size; y0=(r+quiet)*module_size
                draw.rectangle([x0,y0,x0+module_size-1,y0+module_size-1],fill=color)
    buf=_io.BytesIO(); img.save(buf,format='PNG')
    return _b64.b64encode(buf.getvalue()).decode()


try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")
    st.stop()

def run_query(query, params=None):
    try:
        return conn.query(query, params=params, ttl=0)
    except Exception as e:
        st.error(f"خطأ: {e}")
        return pd.DataFrame()

def run_write(query, params=None):
    try:
        with conn.session as s:
            s.execute(text(query), params or {})
            s.commit()
        return True
    except Exception as e:
        st.error(f"خطأ: {e}")
        return False

FACTORY_NAME = "شركة مصنع سُبُل الريادة"
FACTORY_ADDRESS = "الرياض - مدينة الخرج"
FACTORY_CR = "—"
FACTORY_TAX = "—"

raw_materials_list = [
    "راتنج كميائي صنف اول للديزل",
    "راتنج كميائي صنف ٢ للصرف الصحي",
    "ريزن عادي",
    "ألياف (Mat 450)",
    "روفرز (Roving 600)",
    "تيسو (Tissue)",
    "مصلد (Catalyst)",
    "كربونات الكالسيوم",
    "سيليكا (Silica)"
]

def ensure_inventory_rows():
    """يضمن وجود صف لكل مادة في جدول inventory"""
    for mat in raw_materials_list:
        run_write(
            "INSERT INTO inventory(material_name,quantity) VALUES(:m,0) ON CONFLICT(material_name) DO NOTHING",
            {"m": mat})
    # جدول أسعار المخزون
    try:
        run_write("""CREATE TABLE IF NOT EXISTS inventory_prices(
            material_name TEXT PRIMARY KEY,
            unit_price FLOAT DEFAULT 0)""")
        for mat in raw_materials_list:
            run_write(
                "INSERT INTO inventory_prices(material_name,unit_price) VALUES(:m,0) ON CONFLICT(material_name) DO NOTHING",
                {"m": mat})
    except Exception: pass

# تشغيل عند كل إعادة تحميل للتأكد من وجود كل المواد
try:
    ensure_inventory_rows()
except Exception:
    pass

def ensure_workers_columns():
    """يضيف أعمدة إضافية لجداول العمال"""
    for sql in [
        "ALTER TABLE workers ADD COLUMN IF NOT EXISTS base_salary FLOAT DEFAULT 0",
        "ALTER TABLE workers ADD COLUMN IF NOT EXISTS job_title TEXT DEFAULT ''",
        "ALTER TABLE workers ADD COLUMN IF NOT EXISTS phone TEXT DEFAULT ''",
        "ALTER TABLE worker_advances ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''",
        "ALTER TABLE worker_advances ADD COLUMN IF NOT EXISTS created_at DATE DEFAULT CURRENT_DATE",
        """CREATE TABLE IF NOT EXISTS worker_attendance(
            id SERIAL PRIMARY KEY,
            worker_id INTEGER REFERENCES workers(id),
            att_date DATE NOT NULL DEFAULT CURRENT_DATE,
            status TEXT DEFAULT 'حاضر',
            notes TEXT DEFAULT '',
            UNIQUE(worker_id, att_date))""",
        """CREATE TABLE IF NOT EXISTS worker_deductions(
            id SERIAL PRIMARY KEY,
            worker_id INTEGER REFERENCES workers(id),
            amount FLOAT NOT NULL,
            reason TEXT DEFAULT '',
            deduction_date DATE DEFAULT CURRENT_DATE)""",
    ]:
        try:
            run_write(sql)
        except Exception: pass

try:
    ensure_workers_columns()
except Exception:
    pass

def make_tank_label_html(sn, order_id, customer_name, tank_use,
                         tank_capacity, tank_type, delivery_date,
                         factory_name, factory_address, seq, total):
    """صفحة HTML مستقلة لكل خزان — تحتوي QR + كل البيانات"""
    # QR: نص منسق يظهر بوضوح على أي موبايل عند المسح
    def _safe(s):
        """تنظيف النص — يبقي العربي والإنجليزي والأرقام"""
        return str(s).replace('\n',' ').replace('|','_').strip()

    # ترجمة نوع الاستخدام
    _use_map = {'ماء':'Water','صرف':'Sewage','ديزل':'Diesel','حريق':'Fire'}
    _use_en = _use_map.get(str(tank_use), str(tank_use))

    # نص QR مختصر — يضمن قراءة سليمة على أي جهاز
    qr_text = (
        f"SN:{_safe(sn)} ORD:{_safe(order_id)} "
        f"CAP:{_safe(tank_capacity)} USE:{_use_en} "
        f"TYPE:{_safe(tank_type)} DATE:{_safe(delivery_date)} "
        f"SEQ:{seq}/{total}"
    )
    qr_b64 = make_qr_b64(qr_text, color=(30,58,138), module_size=10)
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{width:210mm;height:297mm;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;padding:20mm;}}
.page{{display:flex;flex-direction:column;align-items:center;justify-content:space-between;height:100%;}}
.header{{width:100%;text-align:center;border-bottom:3px solid #1E3A8A;padding-bottom:12px;margin-bottom:16px;}}
.header h1{{color:#1E3A8A;font-size:22px;font-weight:800;}}
.header p{{color:#64748b;font-size:12px;}}
.qr-section{{display:flex;flex-direction:column;align-items:center;gap:16px;flex:1;justify-content:center;}}
.qr-img{{width:220px;height:220px;border:4px solid #1E3A8A;border-radius:12px;}}
.serial{{font-size:22px;font-weight:800;color:#1E3A8A;letter-spacing:2px;text-align:center;}}
.info-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;width:100%;margin-top:16px;}}
.info-card{{background:#f1f5f9;border-radius:8px;padding:12px;border-right:4px solid #1E3A8A;}}
.info-card .lbl{{font-size:10px;color:#94a3b8;margin-bottom:4px;}}
.info-card .val{{font-size:14px;font-weight:700;}}
.seq-badge{{background:#1E3A8A;color:#fff;padding:6px 20px;border-radius:20px;font-size:13px;font-weight:700;}}
.footer{{width:100%;border-top:2px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;margin-top:16px;}}
@media print{{@page{{size:A4;margin:0;}}body{{padding:15mm;}}}}
</style></head><body>
<div class="page">
  <div class="header">
    <h1>🏭 {factory_name}</h1>
    <p>{factory_address}</p>
    <p style="margin-top:6px;font-weight:700;color:#1E3A8A;">بطاقة تعريف خزان فايبرجلاس</p>
  </div>
  <div class="qr-section">
    <img class="qr-img" src="data:image/png;base64,{qr_b64}" alt="QR Code">
    <div class="serial">{sn}</div>
    <div class="seq-badge">خزان {seq} من {total}</div>
    <div class="info-grid">
      <div class="info-card"><div class="lbl">العميل / Customer</div><div class="val">{customer_name}</div></div>
      <div class="info-card"><div class="lbl">رقم الطلبية / Order</div><div class="val">{order_id}</div></div>
      <div class="info-card"><div class="lbl">السعة / Capacity</div><div class="val">{tank_capacity}</div></div>
      <div class="info-card"><div class="lbl">الاستخدام / Use</div><div class="val">{tank_use}</div></div>
      <div class="info-card"><div class="lbl">نوع التركيب / Type</div><div class="val">{tank_type}</div></div>
      <div class="info-card"><div class="lbl">تاريخ التسليم / Date</div><div class="val">{delivery_date}</div></div>
    </div>
  </div>
  <div class="footer">
    <span>🏭 {factory_name} — {factory_address}</span>
    <span>امسح QR للتحقق من البيانات</span>
  </div>
</div>
</body></html>"""

def generate_invoice_number(delivery_id):
    """
    يولّد رقم فاتورة فريد لا يتكرر أبداً.
    يستخدم invoice_id التسلسلي من قاعدة البيانات.
    الشكل: INV-YYYY-NNNNNN
    """
    # تحقق أولاً: هل يوجد فاتورة محفوظة لهذا الأمر؟
    saved = run_query(
        "SELECT invoice_id FROM sales_invoices WHERE delivery_id=:did ORDER BY invoice_id LIMIT 1",
        {"did": delivery_id})
    if not saved.empty:
        iid = int(saved['invoice_id'].iloc[0])
        return f"INV-{datetime.date.today().year}-{iid:06d}"
    # الفاتورة جديدة — احسب الرقم التالي
    max_id = run_query("SELECT COALESCE(MAX(invoice_id),0) as m FROM sales_invoices")
    next_id = int(max_id['m'].iloc[0]) + 1 if not max_id.empty else 1
    return f"INV-{datetime.date.today().year}-{next_id:06d}"

st.set_page_config(page_title="مصنع سُبُل الريادة - ERP v7.0", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [data-testid="stSidebar"], .stApp { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-header { font-size: 26px; color: #1E3A8A; font-weight: bold; border-bottom: 3px solid #FBBF24; padding-bottom: 5px; }
.designer-tag { font-size: 12px; color: #64748B; background: #F1F5F9; padding: 4px 12px; border-radius: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">'
    f'<div class="main-header">🏭 {FACTORY_NAME} — نظام ERP v7.0</div>'
    f'<div class="designer-tag">تصميم المهندس محمد سلامة</div>'
    f'</div>', unsafe_allow_html=True
)

def df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def render_header():
    st.markdown(f"""
    <div style="border:1px solid #CBD5E1;padding:15px;border-radius:8px;background:#fff;margin-bottom:10px;">
        <h2 style="text-align:center;color:#1E3A8A;margin:0;">{FACTORY_NAME}</h2>
        <p style="text-align:center;color:#555;margin:3px 0;">{FACTORY_ADDRESS}</p>
        <p style="text-align:center;color:#555;font-size:12px;margin:0;">س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p>
        <hr style="border-color:#1E3A8A;margin-top:8px;">
    </div>
    """, unsafe_allow_html=True)

def generate_customer_statement_html(customer_name, customer_info, date_from, date_to, orders_data):
    """
    Generates a full printable HTML customer account statement.
    orders_data: list of dicts, each containing order details, deliveries, invoices, payments.
    """
    today_str = datetime.date.today().strftime("%Y/%m/%d")
    date_from_str = str(date_from)
    date_to_str   = str(date_to)

    cr_number  = customer_info.get('cr_number', '—') or '—'
    tax_number = customer_info.get('tax_number', '—') or '—'
    phone      = customer_info.get('phone', '—') or '—'
    address    = customer_info.get('address', '—') or '—'

    grand_contract = sum(o['total_price']   for o in orders_data)
    grand_vat      = grand_contract * 0.15
    grand_total_vat= grand_contract + grand_vat
    grand_adv      = sum(o['advance_paid']  for o in orders_data)
    grand_invoiced = sum(o['total_invoiced'] for o in orders_data)
    grand_paid     = sum(o['total_paid']    for o in orders_data)
    grand_balance  = grand_invoiced - grand_paid
    grand_tanks    = sum(o['qty']           for o in orders_data)
    grand_delivered= sum(o['total_delivered'] for o in orders_data)

    # ---- Build per-order HTML blocks ----
    orders_html = ""
    for ord_ in orders_data:
        oid          = ord_['order_id']
        use_         = ord_['tank_use']
        cap_         = ord_['tank_capacity'] or '—'
        typ_         = ord_['tank_type']
        status_      = ord_['status']
        qty_         = int(ord_['qty'])
        unit_p       = float(ord_['unit_price'])
        total_p      = float(ord_['total_price'])
        adv_p        = float(ord_['advance_paid'])
        rem_bal      = float(ord_['remaining_balance'])
        order_date_  = str(ord_['order_date'])
        delivered_   = int(ord_['total_delivered'])
        rem_del      = qty_ - delivered_
        pct_del      = int(delivered_ / qty_ * 100) if qty_ > 0 else 0
        t_inv        = float(ord_['total_invoiced'])
        t_paid       = float(ord_['total_paid'])
        bal_ord      = t_inv - t_paid

        status_color = "#16a34a" if status_ == "مكتملة" else ("#dc2626" if status_ == "ملغاة" else "#d97706")
        bal_color    = "#dc2626" if bal_ord > 0 else "#16a34a"

        # deliveries rows
        del_rows = ""
        for d in ord_.get('deliveries', []):
            del_rows += f"""<tr>
                <td>{d.get('delivery_id','—')}</td>
                <td>{d.get('delivery_date','—')}</td>
                <td>{int(d.get('shipped_qty',0))}</td>
                <td>{d.get('driver_name','—')}</td>
                <td>{d.get('car_plate','—')}</td>
            </tr>"""
        if not del_rows:
            del_rows = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;">لم يتم تسليم خزانات بعد</td></tr>'

        # invoices rows
        inv_rows = ""
        for inv in ord_.get('invoices', []):
            inv_rows += f"""<tr>
                <td>{inv.get('invoice_id','—')}</td>
                <td>{inv.get('invoice_date','—')}</td>
                <td>{float(inv.get('grand_total',0)):,.2f}</td>
                <td>{float(inv.get('advance_deducted',0)):,.2f}</td>
                <td style="color:#dc2626;font-weight:600;">{float(inv.get('net_required',0)):,.2f}</td>
            </tr>"""
        if not inv_rows:
            inv_rows = '<tr><td colspan="5" style="text-align:center;color:#94a3b8;">لا توجد فواتير</td></tr>'

        # payments rows
        pay_rows = ""
        for pay in ord_.get('payments', []):
            pay_rows += f"""<tr>
                <td>{pay.get('payment_date','—')}</td>
                <td style="color:#16a34a;font-weight:600;">{float(pay.get('amount',0)):,.2f}</td>
                <td>{pay.get('payment_type','—')}</td>
                <td>{pay.get('bank_name','—')}</td>
            </tr>"""
        if not pay_rows:
            pay_rows = '<tr><td colspan="4" style="text-align:center;color:#94a3b8;">لا توجد دفعات مسجلة</td></tr>'

        progress_color = "#16a34a" if pct_del >= 100 else ("#d97706" if pct_del >= 50 else "#dc2626")

        orders_html += f"""
        <div class="order-block">
            <div class="order-header">
                <span class="order-id">📦 {oid}</span>
                <span class="order-status" style="background:{status_color};">{status_}</span>
            </div>

            <!-- بيانات الطلبية -->
            <div class="info-grid">
                <div class="info-item"><span class="info-label">الاستخدام</span><span class="info-value">{use_}</span></div>
                <div class="info-item"><span class="info-label">السعة</span><span class="info-value">{cap_}</span></div>
                <div class="info-item"><span class="info-label">نوع التركيب</span><span class="info-value">{typ_}</span></div>
                <div class="info-item"><span class="info-label">تاريخ الطلبية</span><span class="info-value">{order_date_}</span></div>
                <div class="info-item"><span class="info-label">الكمية المطلوبة</span><span class="info-value">{qty_} خزان</span></div>
                <div class="info-item"><span class="info-label">سعر الخزان</span><span class="info-value">{unit_p:,.2f} ر</span></div>
                <div class="info-item"><span class="info-label">قيمة العقد</span><span class="info-value">{total_p:,.2f} ر</span></div>
                <div class="info-item"><span class="info-label">الدفعة المقدمة</span><span class="info-value">{adv_p:,.2f} ر</span></div>
            </div>

            <!-- شريط التسليم -->
            <div class="progress-section">
                <div class="progress-label">
                    <span>نسبة التسليم: <b>{pct_del}%</b></span>
                    <span>مسلّم: <b>{delivered_}</b> | متبقي: <b>{rem_del}</b> خزان</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width:{pct_del}%;background:{progress_color};"></div>
                </div>
            </div>

            <!-- جدول التسليمات -->
            <div class="section-title">🚚 سجل التسليمات</div>
            <table class="data-table">
                <thead><tr>
                    <th>رقم التسليم</th><th>التاريخ</th><th>الكمية</th><th>السائق</th><th>رقم اللوحة</th>
                </tr></thead>
                <tbody>{del_rows}</tbody>
            </table>

            <!-- جدول الفواتير -->
            <div class="section-title">📄 الفواتير الصادرة</div>
            <table class="data-table">
                <thead><tr>
                    <th>رقم الفاتورة</th><th>التاريخ</th><th>الإجمالي (ر)</th><th>المقدم المخصوم (ر)</th><th>المستحق (ر)</th>
                </tr></thead>
                <tbody>{inv_rows}</tbody>
            </table>

            <!-- جدول الدفعات -->
            <div class="section-title">💵 الدفعات المستلمة</div>
            <table class="data-table">
                <thead><tr>
                    <th>التاريخ</th><th>المبلغ (ر)</th><th>طريقة الدفع</th><th>البنك</th>
                </tr></thead>
                <tbody>{pay_rows}</tbody>
            </table>

            <!-- ملخص الطلبية -->
            <div class="order-summary">
                <div class="summary-box">
                    <div class="summary-label">إجمالي الفواتير</div>
                    <div class="summary-value">{t_inv:,.2f} ر</div>
                </div>
                <div class="summary-box">
                    <div class="summary-label">إجمالي المدفوع</div>
                    <div class="summary-value" style="color:#16a34a;">{t_paid:,.2f} ر</div>
                </div>
                <div class="summary-box" style="border-color:{bal_color};">
                    <div class="summary-label">الرصيد المستحق</div>
                    <div class="summary-value" style="color:{bal_color};">{bal_ord:,.2f} ر</div>
                </div>
            </div>
        </div>
        """

    final_bal_color = "#dc2626" if grand_balance > 0 else "#16a34a"

    html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>كشف حساب — {customer_name}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{ box-sizing:border-box; margin:0; padding:0; }}
body{{
    font-family:'Cairo',sans-serif;
    direction:rtl;
    background:#f8fafc;
    color:#1e293b;
    font-size:13px;
}}
.page{{
    max-width:900px;
    margin:0 auto;
    background:#fff;
    padding:30px;
}}

/* ===== Header ===== */
.factory-header{{
    display:flex;
    justify-content:space-between;
    align-items:center;
    border-bottom:4px solid #1E3A8A;
    padding-bottom:15px;
    margin-bottom:20px;
}}
.factory-logo{{ font-size:28px; }}
.factory-info h1{{ color:#1E3A8A; font-size:20px; margin-bottom:3px; }}
.factory-info p{{ color:#64748b; font-size:11px; margin:1px 0; }}
.doc-meta{{ text-align:left; }}
.doc-meta .doc-title{{
    background:#1E3A8A;
    color:#fff;
    padding:6px 18px;
    border-radius:20px;
    font-size:14px;
    font-weight:700;
    margin-bottom:8px;
    display:inline-block;
}}
.doc-meta p{{ color:#64748b; font-size:11px; text-align:left; }}

/* ===== Customer Info ===== */
.customer-card{{
    background:linear-gradient(135deg,#1E3A8A 0%,#2563eb 100%);
    color:#fff;
    border-radius:12px;
    padding:18px 22px;
    margin-bottom:20px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-wrap:wrap;
    gap:10px;
}}
.customer-card h2{{ font-size:18px; margin-bottom:4px; }}
.customer-card .meta{{ font-size:11px; opacity:0.85; }}
.customer-card .period{{
    background:rgba(255,255,255,0.2);
    border-radius:8px;
    padding:8px 16px;
    text-align:center;
}}
.customer-card .period span{{ display:block; font-size:11px; opacity:0.8; }}
.customer-card .period strong{{ font-size:13px; }}

/* ===== Grand Summary ===== */
.grand-summary{{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:10px;
    margin-bottom:24px;
}}
.gs-card{{
    background:#f1f5f9;
    border-radius:10px;
    padding:12px;
    text-align:center;
    border-top:3px solid #1E3A8A;
}}
.gs-card.danger{{ border-top-color:#dc2626; background:#fef2f2; }}
.gs-card.success{{ border-top-color:#16a34a; background:#f0fdf4; }}
.gs-card.warn{{ border-top-color:#d97706; background:#fffbeb; }}
.gs-label{{ font-size:10px; color:#64748b; margin-bottom:4px; }}
.gs-value{{ font-size:15px; font-weight:700; color:#1e293b; }}
.gs-card.danger .gs-value{{ color:#dc2626; }}
.gs-card.success .gs-value{{ color:#16a34a; }}

/* ===== Order Blocks ===== */
.order-block{{
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:18px;
    margin-bottom:20px;
    page-break-inside:avoid;
}}
.order-header{{
    display:flex;
    justify-content:space-between;
    align-items:center;
    margin-bottom:14px;
}}
.order-id{{ font-size:15px; font-weight:700; color:#1E3A8A; }}
.order-status{{
    color:#fff;
    padding:3px 14px;
    border-radius:20px;
    font-size:11px;
    font-weight:600;
}}
.info-grid{{
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin-bottom:14px;
    background:#f8fafc;
    border-radius:8px;
    padding:12px;
}}
.info-item{{ display:flex; flex-direction:column; }}
.info-label{{ font-size:10px; color:#94a3b8; margin-bottom:2px; }}
.info-value{{ font-size:12px; font-weight:600; color:#1e293b; }}

/* ===== Progress ===== */
.progress-section{{ margin-bottom:14px; }}
.progress-label{{
    display:flex;
    justify-content:space-between;
    font-size:11px;
    color:#475569;
    margin-bottom:5px;
}}
.progress-bar-bg{{
    background:#e2e8f0;
    border-radius:10px;
    height:10px;
    overflow:hidden;
}}
.progress-bar-fill{{
    height:100%;
    border-radius:10px;
    transition:width 0.3s;
}}

/* ===== Tables ===== */
.section-title{{
    font-size:12px;
    font-weight:700;
    color:#1E3A8A;
    margin:12px 0 6px 0;
    padding-right:8px;
    border-right:3px solid #FBBF24;
}}
.data-table{{
    width:100%;
    border-collapse:collapse;
    font-size:11px;
    margin-bottom:10px;
}}
.data-table th{{
    background:#1E3A8A;
    color:#fff;
    padding:7px 8px;
    text-align:center;
    font-weight:600;
}}
.data-table td{{
    padding:6px 8px;
    text-align:center;
    border-bottom:1px solid #f1f5f9;
}}
.data-table tr:nth-child(even){{ background:#f8fafc; }}
.data-table tr:hover{{ background:#eff6ff; }}

/* ===== Order Summary ===== */
.order-summary{{
    display:flex;
    gap:10px;
    margin-top:12px;
    flex-wrap:wrap;
}}
.summary-box{{
    flex:1;
    min-width:120px;
    border:2px solid #e2e8f0;
    border-radius:8px;
    padding:10px;
    text-align:center;
}}
.summary-label{{ font-size:10px; color:#64748b; margin-bottom:4px; }}
.summary-value{{ font-size:14px; font-weight:700; }}

/* ===== Final Balance ===== */
.final-balance{{
    background:#1E3A8A;
    color:#fff;
    border-radius:12px;
    padding:20px 24px;
    margin-top:24px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    flex-wrap:wrap;
    gap:10px;
}}
.final-balance h3{{ font-size:16px; margin-bottom:2px; }}
.final-balance .amount{{ font-size:28px; font-weight:800; }}
.final-balance .amount.zero{{ color:#86efac; }}
.final-balance .amount.owed{{ color:#fca5a5; }}
.final-stat{{ text-align:center; }}
.final-stat .val{{ font-size:16px; font-weight:700; }}
.final-stat .lbl{{ font-size:10px; opacity:0.75; }}

/* ===== Footer ===== */
.footer{{
    margin-top:24px;
    border-top:1px solid #e2e8f0;
    padding-top:12px;
    display:flex;
    justify-content:space-between;
    font-size:10px;
    color:#94a3b8;
}}
.signature-area{{
    margin-top:40px;
    display:flex;
    justify-content:space-between;
    padding:0 30px;
}}
.sig-box{{
    text-align:center;
    width:160px;
}}
.sig-line{{
    border-top:1px solid #94a3b8;
    margin-bottom:6px;
}}
.sig-label{{ font-size:11px; color:#64748b; }}

@media print{{
    body{{ background:#fff; }}
    .page{{ padding:15px; max-width:100%; }}
    .order-block{{ page-break-inside:avoid; }}
}}
</style>
</head>
<body>
<div class="page">

    <!-- رأس الصفحة -->
    <div class="factory-header">
        <div style="display:flex;align-items:center;gap:14px;">
            <div class="factory-logo">🏭</div>
            <div class="factory-info">
                <h1>{FACTORY_NAME}</h1>
                <p>{FACTORY_ADDRESS}</p>
                <p>س.ت: {FACTORY_CR} &nbsp;|&nbsp; الرقم الضريبي: {FACTORY_TAX}</p>
            </div>
        </div>
        <div class="doc-meta">
            <div class="doc-title">كشف حساب عميل</div>
            <p>تاريخ الإصدار: {today_str}</p>
            <p>الفترة: {date_from_str} — {date_to_str}</p>
        </div>
    </div>

    <!-- بيانات العميل -->
    <div class="customer-card">
        <div>
            <h2>👤 {customer_name}</h2>
            <div class="meta">س.ت: {cr_number} &nbsp;|&nbsp; الرقم الضريبي: {tax_number}</div>
        </div>
        <div style="display:flex;gap:16px;flex-wrap:wrap;">
            <div class="period">
                <span>من</span>
                <strong>{date_from_str}</strong>
            </div>
            <div class="period">
                <span>إلى</span>
                <strong>{date_to_str}</strong>
            </div>
            <div class="period">
                <span>عدد الطلبيات</span>
                <strong>{len(orders_data)}</strong>
            </div>
        </div>
    </div>

    <!-- الملخص الإجمالي العلوي -->
    <div class="grand-summary">
        <div class="gs-card">
            <div class="gs-label">إجمالي قيمة العقود</div>
            <div class="gs-value">{grand_contract:,.2f} ر</div>
        </div>
        <div class="gs-card warn">
            <div class="gs-label">إجمالي الفواتير المستحقة</div>
            <div class="gs-value">{grand_invoiced:,.2f} ر</div>
        </div>
        <div class="gs-card success">
            <div class="gs-label">إجمالي المبالغ المحصّلة</div>
            <div class="gs-value">{grand_paid:,.2f} ر</div>
        </div>
        <div class="gs-card danger">
            <div class="gs-label">🔴 الرصيد المستحق</div>
            <div class="gs-value">{grand_balance:,.2f} ر</div>
        </div>
    </div>

    <!-- تفاصيل الطلبيات -->
    {orders_html}

    <!-- الرصيد النهائي -->
    <div class="final-balance">
        <div>
            <h3>📊 الرصيد الإجمالي النهائي</h3>
            <div class="amount {'zero' if grand_balance <= 0 else 'owed'}">{grand_balance:,.2f} ريال</div>
        </div>
        <div style="display:flex;gap:24px;flex-wrap:wrap;">
            <div class="final-stat">
                <div class="val">{grand_tanks}</div>
                <div class="lbl">إجمالي الخزانات المطلوبة</div>
            </div>
            <div class="final-stat">
                <div class="val">{grand_delivered}</div>
                <div class="lbl">الخزانات المسلّمة</div>
            </div>
            <div class="final-stat">
                <div class="val">{grand_tanks - grand_delivered}</div>
                <div class="lbl">المتبقي للتسليم</div>
            </div>
            <div class="final-stat">
                <div class="val">{grand_paid:,.2f} ر</div>
                <div class="lbl">إجمالي المحصّل</div>
            </div>
        </div>
    </div>

    <!-- منطقة التوقيعات -->
    <div class="signature-area">
        <div class="sig-box">
            <div class="sig-line"></div>
            <div class="sig-label">توقيع المحاسب</div>
        </div>
        <div class="sig-box">
            <div class="sig-line"></div>
            <div class="sig-label">توقيع المدير المالي</div>
        </div>
        <div class="sig-box">
            <div class="sig-line"></div>
            <div class="sig-label">ختم الشركة</div>
        </div>
    </div>

    <!-- تذييل الصفحة -->
    <div class="footer">
        <span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span>
        <span>تم الإنشاء بواسطة نظام ERP v7.0 — {today_str}</span>
    </div>

</div>
</body>
</html>"""
    return html


st.sidebar.title("🛠️ الأقسام والعمليات")
menu = st.sidebar.radio("انتقل إلى:", [
    "📊 لوحة التحكم",
    "📦 الطلبيات",
    "🏭 التصنيع",
    "📥 المشتريات والمخزن",
    "💰 الشحن والفواتير",
    "👷 العمال والأجور",
    "📈 النظام المحاسبي",
    "🔍 الاستعلام المتقدم",
    "🗑️ حذف كامل للبيانات"
])

# ==========================================
# [1] لوحة التحكم
# ==========================================
if menu == "📊 لوحة التحكم":
    st.subheader("📈 لوحة التحكم — التقرير المالي")
    c1,c2 = st.columns(2)
    d_start = c1.date_input("من:", datetime.date.today()-datetime.timedelta(days=30))
    d_end   = c2.date_input("إلى:", datetime.date.today())
    st.markdown("---")

    # ======= جلب البيانات =======
    # المبيعات: إجمالي الفواتير (مع الضريبة) في الفترة
    total_sales = float(run_query(
        "SELECT COALESCE(SUM(grand_total),0) as t FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e",
        {"s":d_start,"e":d_end})['t'].iloc[0])

    # ========== تكلفة المواد المستهلكة فعلياً في التصنيع ==========
    # المصدر: production_days — المواد التي صُرفت فعلاً للإنتاج في الفترة
    # وليس المشتريات (المشتريات تذهب للمخزون كأصول)

    # تكلفة المواد من سجلات الإنتاج الفعلي
    prod_mats = run_query("""
        SELECT pd.order_id, pd.actual_qty,
               o.resin_exp, o.mat_exp, o.roving_exp, o.tissue_exp,
               o.catalyst_exp, o.calcium_exp, o.silica_exp
        FROM production_days pd
        JOIN orders o ON pd.order_id = o.order_id
        WHERE pd.status = 'مغلق'
          AND pd.date BETWEEN :s AND :e
    """, {"s": d_start, "e": d_end})

    # جلب أسعار المخزون
    try:
        ip_df = run_query("SELECT material_name, unit_price FROM inventory_prices")
        ip_map = {str(r['material_name']): float(r['unit_price'] or 0) for _,r in ip_df.iterrows()} if not ip_df.empty else {}
    except Exception:
        ip_map = {}

    raw_mat_cost = 0.0
    if not prod_mats.empty:
        mat_keys = [
            ("resin_exp",    list(ip_map.keys())),   # نأخذ أي راتنج
            ("mat_exp",      "ألياف (Mat 450)"),
            ("roving_exp",   "روفرز (Roving 600)"),
            ("tissue_exp",   "تيسو (Tissue)"),
            ("catalyst_exp", "مصلد (Catalyst)"),
            ("calcium_exp",  "كربونات الكالسيوم"),
            ("silica_exp",   "سيليكا (Silica)"),
        ]
        for _, row in prod_mats.iterrows():
            qty_made = float(row['actual_qty'] or 0)
            if qty_made <= 0: continue
            # راتنج - ابحث عن أي مادة راتنج
            resin_price = 0.0
            for k,v in ip_map.items():
                if 'راتنج' in k or 'ريزن' in k:
                    resin_price = v; break
            raw_mat_cost += qty_made * float(row['resin_exp'] or 0) * resin_price
            raw_mat_cost += qty_made * float(row['mat_exp'] or 0)    * ip_map.get("ألياف (Mat 450)", 0)
            raw_mat_cost += qty_made * float(row['roving_exp'] or 0) * ip_map.get("روفرز (Roving 600)", 0)
            raw_mat_cost += qty_made * float(row['tissue_exp'] or 0) * ip_map.get("تيسو (Tissue)", 0)
            raw_mat_cost += qty_made * float(row['catalyst_exp'] or 0) * ip_map.get("مصلد (Catalyst)", 0)
            raw_mat_cost += qty_made * float(row['calcium_exp'] or 0) * ip_map.get("كربونات الكالسيوم", 0)
            raw_mat_cost += qty_made * float(row['silica_exp'] or 0)  * ip_map.get("سيليكا (Silica)", 0)

    raw_mat_cost = round(raw_mat_cost, 2)
    raw_mat_vat  = raw_mat_cost  # تكلفة الإنتاج بدون ضريبة إضافية

    # الرواتب في الفترة
    total_sal = float(run_query(
        "SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",
        {"s":d_start,"e":d_end})['t'].iloc[0])

    # المصاريف التشغيلية
    total_exp = float(run_query(
        "SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",
        {"s":d_start,"e":d_end})['t'].iloc[0])

    # قيمة المخزون المتبقي (أصول وليس مصروف)
    # ======= قيمة المخزون =======
    # ======= قيمة المخزون =======
    # ======= قيمة المخزون =======
    inv_df = run_query("SELECT material_name, quantity FROM inventory ORDER BY material_name")
    inv_value = 0.0

    if not inv_df.empty:
        # جلب الأسعار من جدول inventory_prices المخصص
        try:
            prices_df = run_query("SELECT material_name, unit_price FROM inventory_prices")
            price_map = {str(r['material_name']): float(r['unit_price'] or 0) for _,r in prices_df.iterrows()} if not prices_df.empty else {}
        except Exception:
            price_map = {}
        inv_df['متوسط السعر'] = inv_df['material_name'].map(price_map).fillna(0.0)
        inv_df['القيمة']      = inv_df['quantity'] * inv_df['متوسط السعر']
        inv_value = float(inv_df['القيمة'].sum())

    # ======= الحسابات المالية =======
    total_costs  = raw_mat_cost + total_sal + total_exp
    gross_profit = total_sales - raw_mat_vat
    net_profit   = total_sales - total_costs
    profit_margin= (net_profit / total_sales * 100) if total_sales > 0 else 0

    # ======= بطاقات الأداء =======
    st.markdown("### 💰 ملخص الأداء المالي للفترة")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("📈 إجمالي المبيعات",           f"{total_sales:,.2f} ر")
    r2.metric("🏭 تكلفة المواد المستهلكة", f"{raw_mat_vat:,.2f} ر")
    r3.metric("👷 الرواتب والمصاريف",          f"{total_sal+total_exp:,.2f} ر")
    r4.metric("💵 صافي الربح / الخسارة",
              f"{net_profit:,.2f} ر",
              delta=f"{'ربح ✅' if net_profit>=0 else 'خسارة ❌'} | {profit_margin:.1f}%",
              delta_color="normal" if net_profit>=0 else "inverse")

    st.markdown("---")

    # ======= قائمة الدخل =======
    st.markdown("### 📊 قائمة الدخل التفصيلية")
    income_df = pd.DataFrame([
        {"البيان": "➕ إيرادات المبيعات (مع الضريبة)",            "المبلغ (ريال)": round(total_sales,2)},
        {"البيان": "➖ تكلفة المواد الخام (مع الضريبة)",           "المبلغ (ريال)": round(raw_mat_vat,2)},
        {"البيان": "══ مجمل الربح",                                "المبلغ (ريال)": round(gross_profit,2)},
        {"البيان": "➖ الرواتب وتكاليف العمالة",                   "المبلغ (ريال)": round(total_sal,2)},
        {"البيان": "➖ المصاريف التشغيلية",                         "المبلغ (ريال)": round(total_exp,2)},
        {"البيان": "══ إجمالي التكاليف",                           "المبلغ (ريال)": round(total_costs,2)},
        {"البيان": "💵 صافي الربح / الخسارة",                     "المبلغ (ريال)": round(net_profit,2)},
    ])
    st.dataframe(income_df, use_container_width=True, hide_index=True,
                 column_config={"المبلغ (ريال)": st.column_config.NumberColumn(format="%.2f ر")})

    st.markdown("---")

    # ======= جدول المخزون =======
    st.markdown("### 🏪 قيمة المخزون (أصول)")
    if not inv_df.empty:
        inv_show = inv_df[['material_name','quantity','متوسط السعر','القيمة']].copy()
        inv_show.columns = ['المادة الخام','الكمية','متوسط السعر (ر)','القيمة (ريال)']
        st.dataframe(inv_show, use_container_width=True, hide_index=True,
                     column_config={
                         "الكمية":          st.column_config.NumberColumn(format="%.2f"),
                         "متوسط السعر (ر)": st.column_config.NumberColumn(format="%.2f"),
                         "القيمة (ريال)":   st.column_config.NumberColumn(format="%.2f"),
                     })
        st.success(f"📦 **إجمالي قيمة المخزون: {inv_value:,.2f} ريال**")
        st.caption("لتحديث الأسعار: اذهب لقسم المشتريات والمخزن → ضبط المخزن")
    else:
        st.info("المخزن فارغ")




    st.markdown("---")

    # ======= الطلبيات النشطة =======
    st.write("### 📦 الطلبيات النشطة")
    # تحديث حالة الطلبيات تلقائياً: لو تم تسليم كل الخزانات → مكتملة
    try:
        run_write("""
            UPDATE orders SET status='مكتملة'
            WHERE status='قيد التنفيذ'
            AND qty <= (
                SELECT COALESCE(SUM(shipped_qty),0)
                FROM delivery_orders
                WHERE delivery_orders.order_id = orders.order_id)
        """)
    except Exception: pass

    adf = run_query("""SELECT o.order_id as الطلبية, c.trade_name as العميل,
        o.qty as الكمية, o.total_price as القيمة, o.status as الحالة,
        o.tank_use as الاستخدام,
        COALESCE(o.tank_capacity,'—') as السعة
        FROM orders o JOIN customers c ON o.customer_id=c.id
        WHERE o.status='قيد التنفيذ'
        ORDER BY o.order_date DESC""")
    if not adf.empty:
        st.dataframe(adf, use_container_width=True, hide_index=True,
                     column_config={
                         "القيمة":   st.column_config.NumberColumn(format="%.0f ر"),
                         "الكمية":   st.column_config.NumberColumn(format="%d"),
                         "الطلبية":  st.column_config.TextColumn(width="large"),
                         "العميل":   st.column_config.TextColumn(width="large"),
                         "السعة":    st.column_config.TextColumn(width="medium"),
                     })
    else:
        st.info("لا توجد طلبيات نشطة حالياً")

# ==========================================
# [2] الطلبيات
# ==========================================
elif menu == "📦 الطلبيات":
    st.subheader("📦 منظومة الطلبيات")
    tabs = st.tabs(["➕ طلبية جديدة","✏️ تعديل طلبية","📋 الطلبيات الجارية","💵 دفعات عميل","🔍 كشف حساب عميل"])

    # تبويب 1: طلبية جديدة
    with tabs[0]:
        if 'ok' not in st.session_state: st.session_state.ok = 0
        ok = st.session_state.ok

        with st.expander("👤 ➕ إضافة عميل جديد بسرعة"):
            with st.form("qcf", clear_on_submit=True):
                qc1,qc2 = st.columns(2)
                qcn = qc1.text_input("اسم العميل التجاري:*")
                qcc = qc2.text_input("رقم السجل:")
                qct = st.text_input("الرقم الضريبي:")
                if st.form_submit_button("✅ حفظ العميل"):
                    if qcn:
                        if run_write("INSERT INTO customers(trade_name,cr_number,tax_number) VALUES(:t,:c,:tx) ON CONFLICT(trade_name) DO NOTHING",{"t":qcn,"c":qcc,"tx":qct}):
                            st.success(f"✅ تم إضافة [{qcn}]!")
                    else: st.error("أدخل اسم العميل!")

        auto_code = f"SUBUL-ORD-{datetime.date.today().year}-{random.randint(1000,9999)}"
        order_id_f = st.text_input("كود الطلبية:", value=auto_code, key=f"oid_{ok}")
        cdf = run_query("SELECT id,trade_name FROM customers ORDER BY trade_name")
        if cdf.empty:
            st.warning("⚠️ أضف عميلاً أولاً من الأعلى.")
            cust_sel = None
        else:
            cust_sel = st.selectbox("اختر العميل:", cdf['trade_name'].tolist(), key=f"cs_{ok}")
        c1,c2,c3 = st.columns(3)
        t_use = c1.selectbox("استخدام الخزان:", ["ماء","صرف","ديزل","حريق"], key=f"tu_{ok}")
        t_cap = c2.text_input("السعة:", key=f"tc_{ok}")
        t_typ = c3.selectbox("نوع التركيب:", ["دفّان","فوق الأرض"], key=f"tt_{ok}")
        c4,c5 = st.columns(2)
        qty_f = c4.number_input("عدد الخزانات:", min_value=1, value=1, key=f"qty_{ok}")
        uprice_f = c5.number_input("سعر الخزان (ريال):", min_value=0.0, value=0.0, key=f"up_{ok}")
        total_val = qty_f * uprice_f
        adv_mode = st.selectbox("طريقة المقدم:", ["مبلغ بالريال","نسبة مئوية (%)"], key=f"am_{ok}")
        adv_val = st.number_input("قيمة المقدم:", min_value=0.0, value=0.0, key=f"av_{ok}")
        net_adv = (total_val*adv_val/100) if adv_mode=="نسبة مئوية (%)" else adv_val
        remaining = total_val - net_adv
        st.markdown(f"💰 **إجمالي:** {total_val:,.2f} | 🟢 **المقدم:** {net_adv:,.2f} | 🔴 **المتبقي:** {remaining:,.2f}")
        st.write("---")
        st.markdown("**كميات المواد المعيارية لخزان واحد:**")
        resin_types = ["راتنج كميائي صنف اول للديزل","راتنج كميائي صنف ٢ للصرف الصحي","ريزن عادي"]
        resin_type_sel = st.selectbox("نوع الراتنج المستخدم:", resin_types, key=f"rtype_{ok}")
        x1,x2,x3 = st.columns(3)
        r_ex = x1.number_input("راتنج (كجم):", min_value=0.0, value=0.0, key=f"re_{ok}")
        m_ex = x2.number_input("ألياف Mat (كجم):", min_value=0.0, value=0.0, key=f"me_{ok}")
        v_ex = x3.number_input("روفرز (كجم):", min_value=0.0, value=0.0, key=f"ve_{ok}")
        t_ex = x1.number_input("تيسو (م²):", min_value=0.0, value=0.0, key=f"te_{ok}")
        ca_ex = x2.number_input("مصلد (كجم):", min_value=0.0, value=0.0, key=f"cae_{ok}")
        cc_ex = x3.number_input("كالسيوم (كجم):", min_value=0.0, value=0.0, key=f"cce_{ok}")
        s_ex = x1.number_input("سيليكا (كجم):", min_value=0.0, value=0.0, key=f"se_{ok}")
        # ========== فحص المخزن مقابل المواد المطلوبة ==========
        if qty_f > 0 and (r_ex+m_ex+v_ex+t_ex+ca_ex+cc_ex+s_ex) > 0:
            st.info(f"📊 إجمالي المواد ({qty_f} خزان): راتنج {r_ex*qty_f:.0f} | ألياف {m_ex*qty_f:.0f} | روفرز {v_ex*qty_f:.0f} | تيسو {t_ex*qty_f:.0f} | مصلد {ca_ex*qty_f:.0f} | كالسيوم {cc_ex*qty_f:.0f} | سيليكا {s_ex*qty_f:.0f}")

            # احتياج هذه الطلبية — يستخدم نوع الراتنج المختار
            this_order_needs = {
                resin_type_sel: r_ex * qty_f,
                "ألياف (Mat 450)":              m_ex * qty_f,
                "روفرز (Roving 600)":           v_ex * qty_f,
                "تيسو (Tissue)":                t_ex * qty_f,
                "مصلد (Catalyst)":              ca_ex * qty_f,
                "كربونات الكالسيوم":            cc_ex * qty_f,
                "سيليكا (Silica)":              s_ex * qty_f,
            }
            # جلب رصيد المخزن الحالي
            inv_now = run_query("SELECT material_name,quantity FROM inventory")
            inv_dict = {r['material_name']: float(r['quantity']) for _,r in inv_now.iterrows()} if not inv_now.empty else {}

            # مقارنة مباشرة بالمخزن الفعلي — بدون خصم "محجوز"
            # لأن المخزن يُخصم فعلياً عند بدء كل وردية إنتاج
            shortages = {}
            check_rows = []
            for mat, needed in this_order_needs.items():
                if needed <= 0: continue
                stock    = inv_dict.get(mat, 0.0)
                shortage = max(0.0, needed - stock)
                status_icon = "✅" if shortage == 0 else "🔴"
                check_rows.append({
                    "المادة":    mat,
                    "المخزون":  f"{stock:,.2f}",
                    "مطلوب":    f"{needed:,.2f}",
                    "العجز":    f"{shortage:,.2f}",
                    "الحالة":   status_icon
                })
                if shortage > 0:
                    shortages[mat] = shortage

            with st.expander("📦 فحص توافر المواد الخام", expanded=bool(shortages)):
                st.dataframe(pd.DataFrame(check_rows), use_container_width=True, hide_index=True)
                if shortages:
                    st.error(f"⚠️ يوجد عجز في {len(shortages)} مادة خام!")
                    if 'show_po' not in st.session_state: st.session_state.show_po = False
                    if st.button("🛒 نعم، أريد عمل أمر شراء للمواد الناقصة", key=f"po_btn_{ok}"):
                        st.session_state.show_po = True
                    if st.session_state.show_po:
                        sdf_po = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
                        if sdf_po.empty:
                            st.warning("لا يوجد موردون — أضف موردين أولاً من قسم المشتريات.")
                        else:
                            po_sup = st.selectbox("اختر المورد:", sdf_po['original_name'].tolist(), key=f"po_sup_{ok}")
                            po_sup_id = int(sdf_po[sdf_po['original_name']==po_sup]['id'].iloc[0])
                            st.markdown("**المواد الناقصة المقترح شراؤها:**")
                            po_rows = []
                            for mat, qty_short in shortages.items():
                                po_rows.append({"المادة":mat, "الكمية المقترحة":f"{qty_short:,.3f}", "الوحدة":"كجم/م²"})
                            st.dataframe(pd.DataFrame(po_rows), use_container_width=True, hide_index=True)
                            if st.button("✅ تأكيد إصدار أمر الشراء", key=f"po_confirm_{ok}", type="primary"):
                                today_po = datetime.date.today().strftime("%Y/%m/%d")
                                po_html_rows = "".join(f'<tr><td style="padding:8px 10px;border:1px solid #e2e8f0;">{m}</td><td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;">{q:,.3f}</td><td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">كجم/م²</td></tr>' for m,q in shortages.items())
                                po_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}} body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:14px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#d97706;color:#fff;padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;}}
.info-box{{background:#fef3c7;border-radius:10px;padding:14px;margin-bottom:18px;border-right:4px solid #d97706;}}
table{{width:100%;border-collapse:collapse;margin-bottom:18px;}}
thead th{{background:#1E3A8A;color:#fff;padding:9px 10px;text-align:center;font-size:12px;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:26px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
  <div style="text-align:left;"><div class="badge">أمر شراء مواد خام</div><p style="margin-top:8px;color:#64748b;font-size:11px;">التاريخ: {today_po}</p></div>
</div>
<div class="info-box">
  <p><b>المورد:</b> {po_sup}</p>
  <p><b>سبب الأمر:</b> عجز مواد خام لطلبية جديدة</p>
  <p><b>التاريخ:</b> {today_po}</p>
</div>
<table><thead><tr><th>المادة الخام</th><th>الكمية المطلوبة</th><th>الوحدة</th></tr></thead><tbody>{po_html_rows}</tbody></table>
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {today_po}</span></div>
</body></html>"""
                                st.session_state[f'po_html_{ok}'] = po_html
                                st.success(f"✅ تم إصدار أمر الشراء للمورد: {po_sup}")
                            if st.session_state.get(f'po_html_{ok}'):
                                st.download_button("🖨️ طباعة أمر الشراء (HTML)",
                                    st.session_state[f'po_html_{ok}'].encode('utf-8'),
                                    f"PO_{datetime.date.today()}.html",
                                    "text/html; charset=utf-8",
                                    key=f"dl_po_{ok}")
                                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")
                else:
                    st.success("✅ المخزن يكفي لهذه الطلبية مع الطلبيات الجارية.")

        if st.button("🚀 حفظ الطلبية", key=f"save_{ok}"):
            if not cust_sel: st.error("أضف عميلاً أولاً!")
            elif uprice_f==0: st.error("أدخل سعر الخزان!")
            else:
                cid = int(cdf[cdf['trade_name']==cust_sel]['id'].iloc[0])
                if run_write("""INSERT INTO orders(order_id,customer_id,tank_use,tank_capacity,tank_type,qty,unit_price,total_price,advance_paid,remaining_balance,resin_exp,mat_exp,roving_exp,tissue_exp,catalyst_exp,calcium_exp,silica_exp)
                    VALUES(:oid,:cid,:tu,:tc,:tt,:qty,:up,:tp,:ap,:rb,:re,:me,:ve,:te,:cae,:cce,:se)""",
                    {"oid":order_id_f,"cid":cid,"tu":t_use,"tc":t_cap,"tt":t_typ,"qty":qty_f,"up":uprice_f,
                     "tp":total_val,"ap":net_adv,"rb":remaining,"re":r_ex,"me":m_ex,"ve":v_ex,"te":t_ex,"cae":ca_ex,"cce":cc_ex,"se":s_ex}):
                    # حفظ نوع الراتنج في session_state للمرجعية
                    st.session_state[f'resin_type_{order_id_f}'] = resin_type_sel
                    st.success("✅ تم حفظ الطلبية!")
                    st.session_state.ok += 1
                    st.rerun()

    # تبويب 2: تعديل طلبية كاملة
    with tabs[1]:
        ode = run_query("SELECT o.order_id,c.trade_name,o.qty,o.unit_price,o.advance_paid,o.tank_use,o.tank_capacity,o.tank_type,o.status FROM orders o JOIN customers c ON o.customer_id=c.id ORDER BY o.order_date DESC")
        if ode.empty:
            st.info("لا توجد طلبيات.")
        else:
            sel_e = st.selectbox("اختر الطلبية:", [f"{r['order_id']} | {r['trade_name']}" for _,r in ode.iterrows()], key="esel")
            oid_e = sel_e.split(" | ")[0]
            rr = ode[ode['order_id']==oid_e].iloc[0]
            st.info(f"📋 الطلبية الحالية: الكمية={int(rr['qty'])} | السعر={float(rr['unit_price']):,.2f} | المقدم={float(rr['advance_paid']):,.2f} | الاستخدام={rr['tank_use']} | السعة={rr['tank_capacity'] or '—'} | النوع={rr['tank_type']}")
            e1,e2 = st.columns(2)
            new_qty = e1.number_input("الكمية:", min_value=1, value=int(rr['qty']), key="eq")
            new_up = e2.number_input("سعر الخزان (ريال):", min_value=0.0, value=float(rr['unit_price']), key="eup")
            new_total = new_qty * new_up
            e3,e4 = st.columns(2)
            new_adv = e3.number_input("المقدم:", min_value=0.0, value=float(rr['advance_paid']), key="eadv")
            new_rem = new_total - new_adv
            e4.metric("المتبقي:", f"{new_rem:,.2f} ر")
            ul=["ماء","صرف","ديزل","حريق"]; tl=["دفّان","فوق الأرض"]; sl=["قيد التنفيذ","مكتملة","ملغاة"]
            e5,e6,e7 = st.columns(3)
            new_use = e5.selectbox("استخدام الخزان:", ul, index=ul.index(rr['tank_use']) if rr['tank_use'] in ul else 0, key="eu")
            import pandas as _pd
            _raw_cap = rr['tank_capacity']
            _cur_cap = "" if (_raw_cap is None or str(_raw_cap).strip() in ("None","nan","NaN","")) else str(_raw_cap).strip()
            new_cap = e6.text_input("💧 سعة الخزان (مثال: 8000 لتر):", value=_cur_cap, key="ec",
                                     help="أدخل السعة مثل: 5000 لتر أو 10000L")
            if not new_cap:
                e6.warning("⚠️ لم تُدخل سعة الخزان")
            new_typ = e7.selectbox("نوع التركيب:", tl, index=tl.index(rr['tank_type']) if rr['tank_type'] in tl else 0, key="ety")
            new_stat = st.selectbox("الحالة:", sl, index=sl.index(rr['status']) if rr['status'] in sl else 0, key="es")

            # فحص المواد عند تغيير الكمية
            if new_qty != int(rr['qty']) and float(rr.get('resin_exp') or 0) > 0:
                st.markdown("##### 📦 إعادة فحص المواد الخام بعد التعديل")
                _edit_needs = {
                    "راتنج كميائي صنف اول للديزل": float(rr.get('resin_exp') or 0) * new_qty,
                    "ألياف (Mat 450)":              float(rr.get('mat_exp') or 0) * new_qty,
                    "روفرز (Roving 600)":           float(rr.get('roving_exp') or 0) * new_qty,
                    "تيسو (Tissue)":                float(rr.get('tissue_exp') or 0) * new_qty,
                    "مصلد (Catalyst)":              float(rr.get('catalyst_exp') or 0) * new_qty,
                    "كربونات الكالسيوم":            float(rr.get('calcium_exp') or 0) * new_qty,
                    "سيليكا (Silica)":              float(rr.get('silica_exp') or 0) * new_qty,
                }
                _edit_inv = run_query("SELECT material_name,quantity FROM inventory")
                _edit_inv_dict = {r['material_name']:float(r['quantity']) for _,r in _edit_inv.iterrows()} if not _edit_inv.empty else {}
                _edit_shortages = {}
                _edit_rows = []
                for mat,needed in _edit_needs.items():
                    if needed <= 0: continue
                    stock = _edit_inv_dict.get(mat,0.0)
                    short = max(0.0, needed - stock)
                    _edit_rows.append({"المادة":mat,"المخزون":f"{stock:,.2f}","المطلوب":f"{needed:,.2f}","العجز":f"{short:,.2f}","الحالة":"✅" if short==0 else "🔴"})
                    if short > 0: _edit_shortages[mat] = short
                st.dataframe(pd.DataFrame(_edit_rows), use_container_width=True, hide_index=True)
                if _edit_shortages:
                    st.error(f"⚠️ يوجد عجز في {len(_edit_shortages)} مادة خام بعد تعديل الكمية!")
                    _edit_sdf = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
                    if not _edit_sdf.empty:
                        _edit_sup = st.selectbox("المورد لأمر الشراء:", _edit_sdf['original_name'].tolist(), key="edit_po_sup")
                        # توليد أمر الشراء مباشرة بدون ضغط زر إضافي
                        _ep_rows = "".join(
                            f'''<tr>
                              <td style="padding:8px 10px;border:1px solid #e2e8f0;">{m}</td>
                              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;color:#dc2626;">{q:,.3f}</td>
                              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">كجم / م²</td>
                            </tr>'''
                            for m,q in _edit_shortages.items())
                        _today_ep = datetime.date.today().strftime("%Y/%m/%d")
                        _edit_po_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #d97706;padding-bottom:14px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#d97706;color:#fff;padding:6px 18px;border-radius:20px;font-size:13px;font-weight:700;}}
.info-box{{background:#fef3c7;border-radius:10px;padding:14px;margin-bottom:18px;border-right:4px solid #d97706;}}
.info-box p{{font-size:12px;margin:3px 0;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px;text-align:center;font-size:12px;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:36px;}}
.sig-box{{text-align:center;width:150px;}} .sig-line{{border-top:2px solid #1e293b;margin-bottom:6px;height:34px;}}
.sig-lbl{{font-size:11px;color:#64748b;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:26px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p></div>
  <div style="text-align:left;"><div class="badge">أمر توريد مواد خام</div><p style="color:#64748b;font-size:11px;margin-top:8px;">التاريخ: {_today_ep}</p></div>
</div>
<div class="info-box">
  <p><b>المورد:</b> {_edit_sup}</p>
  <p><b>الطلبية:</b> {sel_e}</p>
  <p><b>سبب الأمر:</b> زيادة عدد الخزانات من {int(rr['qty'])} إلى {new_qty} خزان</p>
  <p><b>التاريخ:</b> {_today_ep}</p>
</div>
<table>
  <thead><tr><th>المادة الخام</th><th>الكمية الناقصة</th><th>الوحدة</th></tr></thead>
  <tbody>{_ep_rows}</tbody>
</table>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">أمين المخزن</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">مدير المشتريات</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">المدير العام</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {_today_ep}</span></div>
</body></html>"""
                        st.download_button(
                            "🖨️ تنزيل أمر توريد المواد الناقصة (HTML)",
                            _edit_po_html.encode('utf-8'),
                            f"PO_edit_{sel_e}_{datetime.date.today()}.html",
                            "text/html; charset=utf-8",
                            key="dl_edit_po",
                            type="primary")
                        st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")
                else:
                    st.success("✅ المخزن كافٍ للكمية الجديدة — يمكن حفظ التعديل")


            if new_stat == "ملغاة":
                st.error("⚠️ تحذير: اختيار 'ملغاة' سيحذف الطلبية من جميع السجلات نهائياً!")

            if st.button("💾 حفظ التعديلات"):
                if new_stat == "ملغاة":
                    for tbl in ["sales_invoices","customer_payments","delivery_orders","production_tanks","production_days","general_expenses"]:
                        run_write(f"DELETE FROM {tbl} WHERE order_id=:oid", {"oid":oid_e})
                    run_write("DELETE FROM orders WHERE order_id=:oid", {"oid":oid_e})
                    st.success(f"✅ تم حذف الطلبية {oid_e} بالكامل!")
                    st.rerun()
                else:
                    if run_write("UPDATE orders SET qty=:qty,unit_price=:up,total_price=:tp,advance_paid=:ap,remaining_balance=:rb,tank_use=:tu,tank_capacity=:tc,tank_type=:tt,status=:s WHERE order_id=:oid",
                        {"qty":new_qty,"up":new_up,"tp":new_total,"ap":new_adv,"rb":new_rem,"tu":new_use,"tc":new_cap,"tt":new_typ,"s":new_stat,"oid":oid_e}):
                        st.success("✅ تم تحديث الطلبية!")
                        st.rerun()

    # تبويب 3: الطلبيات الجارية - Dashboard احترافي
    with tabs[2]:
        active_orders = run_query("""
            SELECT o.order_id, c.trade_name, o.tank_use, o.tank_capacity, o.tank_type,
                   o.qty, o.unit_price, o.total_price, o.advance_paid, o.remaining_balance,
                   o.order_date, o.status
            FROM orders o JOIN customers c ON o.customer_id=c.id
            WHERE o.status='قيد التنفيذ' ORDER BY o.order_date DESC""")

        if active_orders.empty:
            st.info("لا توجد طلبيات جارية حالياً.")
        else:
            st.markdown(f"### 📊 إجمالي الطلبيات الجارية: **{len(active_orders)}** طلبية")

            # ملخص سريع في الأعلى
            total_contracts = float(active_orders['total_price'].sum())
            total_adv = float(active_orders['advance_paid'].sum())
            total_rem = float(active_orders['remaining_balance'].sum())
            total_tanks = int(active_orders['qty'].sum())
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("إجمالي قيمة العقود", f"{total_contracts:,.0f} ر")
            m2.metric("إجمالي المقدمات", f"{total_adv:,.0f} ر")
            m3.metric("إجمالي المتبقي", f"{total_rem:,.0f} ر")
            m4.metric("إجمالي الخزانات المطلوبة", f"{total_tanks} خزان")
            st.markdown("---")

            for _, ord_r in active_orders.iterrows():
                oid_a = ord_r['order_id']

                # جلب بيانات التصنيع
                prod_done = run_query("SELECT COALESCE(SUM(actual_qty),0) as t FROM production_days WHERE order_id=:oid AND status='مغلق'",{"oid":oid_a})
                tanks_made = int(prod_done['t'].iloc[0]) if not prod_done.empty else 0
                tanks_remaining_prod = int(ord_r['qty']) - tanks_made

                # جلب بيانات التسليم
                del_data = run_query("SELECT COALESCE(SUM(shipped_qty),0) as t FROM delivery_orders WHERE order_id=:oid",{"oid":oid_a})
                tanks_delivered = int(del_data['t'].iloc[0]) if not del_data.empty else 0
                tanks_remaining_del = int(ord_r['qty']) - tanks_delivered

                # جلب الدفعات المستلمة
                pay_data = run_query("""SELECT COALESCE(SUM(amount),0) as total,
                    MAX(payment_date) as last_date FROM customer_payments
                    WHERE order_id=:oid""",{"oid":oid_a})
                total_received = float(pay_data['total'].iloc[0]) if not pay_data.empty else 0.0
                last_pay_date = pay_data['last_date'].iloc[0] if not pay_data.empty else None
                real_remaining = float(ord_r['total_price']) * 1.15 - float(ord_r['advance_paid']) - total_received

                # نسب الإنجاز
                pct_prod = min(100, int(tanks_made/int(ord_r['qty'])*100)) if int(ord_r['qty'])>0 else 0
                pct_del = min(100, int(tanks_delivered/int(ord_r['qty'])*100)) if int(ord_r['qty'])>0 else 0

                # عرض بطاقة الطلبية
                _cap_a = str(ord_r['tank_capacity'] or '—').strip()
                _cap_a = _cap_a if _cap_a not in ('None','nan','') else '—'
                with st.expander(f"📦 {oid_a} | {ord_r['trade_name']} | {int(ord_r['qty'])} خزان | {ord_r['tank_use']} {_cap_a} | القيمة: {float(ord_r['total_price']):,.0f} ر", expanded=False):

                    # القسم 1: بيانات العقد
                    st.markdown("#### 📋 بيانات العقد")
                    c1,c2,c3,c4,c5 = st.columns(5)
                    c1.metric("رقم الطلبية", oid_a)
                    c2.metric("العميل", ord_r['trade_name'])
                    c3.metric("الاستخدام", f"{ord_r['tank_use']} - {ord_r['tank_capacity'] or '—'}")
                    c4.metric("النوع", str(ord_r['tank_type']))
                    c5.metric("تاريخ الطلبية", str(ord_r['order_date']))

                    c6,c7,c8,c9 = st.columns(4)
                    c6.metric("قيمة العقد", f"{float(ord_r['total_price']):,.2f} ر")
                    c7.metric("الدفعة المقدمة", f"{float(ord_r['advance_paid']):,.2f} ر")
                    c8.metric("المتبقي من العقد", f"{float(ord_r['remaining_balance']):,.2f} ر")
                    c9.metric("سعر الخزان", f"{float(ord_r['unit_price']):,.2f} ر")

                    st.markdown("---")

                    # القسم 2: وضع التصنيع
                    st.markdown("#### 🏭 وضع التصنيع")
                    p1,p2,p3,p4 = st.columns(4)
                    p1.metric("الكمية المطلوبة", f"{int(ord_r['qty'])} خزان")
                    p2.metric("المصنّع فعلياً", f"{tanks_made} خزان")
                    p3.metric("المتبقي للتصنيع", f"{tanks_remaining_prod} خزان")
                    p4.metric("نسبة إنجاز التصنيع", f"{pct_prod}%")

                    # شريط تقدم التصنيع
                    st.markdown(f"""<div style="background:#e2e8f0;border-radius:8px;height:16px;overflow:hidden;margin:4px 0 2px 0">
<div style="background:{'#16a34a' if pct_prod==100 else '#d97706' if pct_prod>=50 else '#dc2626'};width:{min(100,pct_prod)}%;height:100%;border-radius:8px;"></div></div>
<small style="color:#64748b">🏭 التصنيع: {pct_prod}%</small>""", unsafe_allow_html=True)

                    # آخر الورديات
                    shifts = run_query("""SELECT date,planned_qty,actual_qty,status
                        FROM production_days WHERE order_id=:oid ORDER BY date DESC LIMIT 5""",{"oid":oid_a})
                    if not shifts.empty:
                        st.write("**آخر الورديات:**")
                        st.dataframe(shifts.rename(columns={"date":"التاريخ","planned_qty":"المخطط","actual_qty":"الفعلي","status":"الحالة"}), use_container_width=True)

                    st.markdown("---")

                    # القسم 3: وضع التسليم
                    st.markdown("#### 🚚 وضع التسليم")
                    d1,d2,d3,d4 = st.columns(4)
                    d1.metric("الكمية المطلوبة", f"{int(ord_r['qty'])} خزان")
                    d2.metric("المسلّم للعميل", f"{tanks_delivered} خزان")
                    d3.metric("المتبقي للتسليم", f"{tanks_remaining_del} خزان")
                    d4.metric("نسبة إنجاز التسليم", f"{pct_del}%")

                    st.markdown(f"""<div style="background:#e2e8f0;border-radius:8px;height:16px;overflow:hidden;margin:4px 0 2px 0">
<div style="background:{'#16a34a' if pct_del==100 else '#2563eb' if pct_del>=50 else '#94a3b8'};width:{min(100,pct_del)}%;height:100%;border-radius:8px;"></div></div>
<small style="color:#64748b">🚚 التسليم: {pct_del}%</small>""", unsafe_allow_html=True)

                    # سجل التسليمات
                    deliveries = run_query("""SELECT delivery_date,shipped_qty,driver_name,car_plate
                        FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_date DESC""",{"oid":oid_a})
                    if not deliveries.empty:
                        st.write("**سجل التسليمات:**")
                        st.dataframe(deliveries.rename(columns={"delivery_date":"التاريخ","shipped_qty":"الكمية","driver_name":"السائق","car_plate":"اللوحة"}), use_container_width=True)
                    else:
                        st.info("لم يتم تسليم خزانات بعد.")

                    st.markdown("---")

                    # القسم 4: الوضع المالي التفصيلي
                    st.markdown("#### 💰 الوضع المالي التفصيلي")

                    # جلب كل الدفعات مع التواريخ
                    pays = run_query("""SELECT payment_date, amount, payment_type, bank_name
                        FROM customer_payments WHERE order_id=:oid ORDER BY payment_date ASC""",{"oid":oid_a})
                    total_pays = float(pays['amount'].sum()) if not pays.empty else 0.0

                    # الحساب الصحيح
                    contract_val = float(ord_r['total_price'])
                    contract_with_vat = contract_val * 1.15
                    advance = float(ord_r['advance_paid'])
                    total_collected = advance + total_pays
                    real_balance = contract_with_vat - total_collected

                    # عرض ملخص مالي
                    f1,f2,f3 = st.columns(3)
                    f1.metric("قيمة العقد بدون ضريبة", f"{contract_val:,.2f} ر")
                    f2.metric("ضريبة القيمة المضافة 15%", f"{contract_val*0.15:,.2f} ر")
                    f3.metric("إجمالي العقد شامل الضريبة", f"{contract_with_vat:,.2f} ر")

                    st.markdown("---")

                    # جدول حركة الحساب التفصيلي
                    st.markdown("**📊 حركة الحساب التفصيلية:**")
                    account_rows = []
                    running_balance = contract_with_vat

                    # السطر الأول: إجمالي العقد
                    account_rows.append({
                        "التاريخ": str(ord_r['order_date']),
                        "البيان": "إجمالي قيمة العقد شامل الضريبة",
                        "مدين (مستحق علينا)": f"{contract_with_vat:,.2f}",
                        "دائن (مدفوع)": "—",
                        "الرصيد المتبقي": f"{running_balance:,.2f}"
                    })

                    # الدفعة المقدمة
                    if advance > 0:
                        running_balance -= advance
                        account_rows.append({
                            "التاريخ": str(ord_r['order_date']),
                            "البيان": "دفعة مقدمة عند التعاقد",
                            "مدين (مستحق علينا)": "—",
                            "دائن (مدفوع)": f"{advance:,.2f}",
                            "الرصيد المتبقي": f"{running_balance:,.2f}"
                        })

                    # باقي الدفعات
                    if not pays.empty:
                        for _, pay_row in pays.iterrows():
                            running_balance -= float(pay_row['amount'])
                            bank_info = f" | {pay_row['bank_name']}" if pay_row['bank_name'] else ""
                            account_rows.append({
                                "التاريخ": str(pay_row['payment_date']),
                                "البيان": f"دفعة مستلمة - {pay_row['payment_type']}{bank_info}",
                                "مدين (مستحق علينا)": "—",
                                "دائن (مدفوع)": f"{float(pay_row['amount']):,.2f}",
                                "الرصيد المتبقي": f"{running_balance:,.2f}"
                            })

                    acc_df = pd.DataFrame(account_rows)
                    st.dataframe(acc_df, use_container_width=True)

                    # ملخص مالي نهائي
                    st.markdown("---")
                    fa1,fa2,fa3,fa4 = st.columns(4)
                    fa1.metric("المقدم المستلم", f"{advance:,.2f} ر", help=f"تاريخ العقد: {ord_r['order_date']}")
                    fa2.metric("الدفعات اللاحقة", f"{total_pays:,.2f} ر", help=f"عدد الدفعات: {len(pays)}")
                    fa3.metric("إجمالي المحصّل", f"{total_collected:,.2f} ر")
                    if real_balance > 0:
                        fa4.metric("🔴 الرصيد المستحق", f"{real_balance:,.2f} ر")
                    else:
                        fa4.metric("🟢 تم السداد الكامل", f"{abs(real_balance):,.2f} ر زيادة")

                    st.markdown("---")

                    # ملخص الطلبية
                    st.markdown("#### 📊 ملخص الطلبية")
                    color_prod = "🟢" if pct_prod==100 else ("🟡" if pct_prod>50 else "🔴")
                    color_del = "🟢" if pct_del==100 else ("🟡" if pct_del>50 else "🔴")
                    color_fin = "🟢" if real_remaining<=0 else ("🟡" if real_remaining < float(ord_r['total_price'])*0.5 else "🔴")
                    st.markdown(f"""
                    | البند | التفاصيل | الحالة |
                    |-------|----------|--------|
                    | التصنيع | {tanks_made} من {int(ord_r['qty'])} خزان ({pct_prod}%) | {color_prod} |
                    | التسليم | {tanks_delivered} من {int(ord_r['qty'])} خزان ({pct_del}%) | {color_del} |
                    | التحصيل | مستحق {real_remaining:,.0f} ريال | {color_fin} |
                    """)

            # تنزيل ملخص كل الطلبيات
            summary_rows = []
            for _, ord_r in active_orders.iterrows():
                oid_a = ord_r['order_id']
                pm = run_query("SELECT COALESCE(SUM(actual_qty),0) as t FROM production_days WHERE order_id=:oid AND status='مغلق'",{"oid":oid_a})
                dm = run_query("SELECT COALESCE(SUM(shipped_qty),0) as t FROM delivery_orders WHERE order_id=:oid",{"oid":oid_a})
                pm2 = run_query("SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE order_id=:oid",{"oid":oid_a})
                _pm2_val = float(pm2['t'].iloc[0]) if not pm2.empty else 0.0
                _adv_val = float(ord_r['advance_paid'])
                _contract_vat = float(ord_r['total_price']) * 1.15
                summary_rows.append({
                    "رقم الطلبية": oid_a,
                    "العميل": ord_r['trade_name'],
                    "الكمية": int(ord_r['qty']),
                    "المصنّع": int(pm['t'].iloc[0]) if not pm.empty else 0,
                    "المسلّم": int(dm['t'].iloc[0]) if not dm.empty else 0,
                    "قيمة العقد": float(ord_r['total_price']),
                    "ضريبة 15%": float(ord_r['total_price']) * 0.15,
                    "الإجمالي مع الضريبة": _contract_vat,
                    "الدفعة المقدمة": _adv_val,
                    "الدفعات اللاحقة": _pm2_val,
                    "إجمالي المحصّل": _adv_val + _pm2_val,
                    "المستحق": _contract_vat - _adv_val - _pm2_val
                })
            if summary_rows:
                sum_df = pd.DataFrame(summary_rows)
                st.markdown("---")
                st.markdown("### 📋 جدول ملخص كل الطلبيات الجارية")

                # بناء جدول HTML كامل للطباعة
                today_str = datetime.date.today().strftime("%Y/%m/%d")
                rows_html = ""
                for _, r in sum_df.iterrows():
                    rows_html += f"""
                    <tr>
                        <td>{r["رقم الطلبية"]}</td>
                        <td>{r["العميل"]}</td>
                        <td>{int(r["الكمية"])}</td>
                        <td>{int(r["المصنّع"])}</td>
                        <td>{int(r["المسلّم"])}</td>
                        <td>{float(r["قيمة العقد"]):,.2f}</td>
                        <td>{float(r["ضريبة 15%"]):,.2f}</td>
                        <td>{float(r["الإجمالي مع الضريبة"]):,.2f}</td>
                        <td>{float(r["الدفعة المقدمة"]):,.2f}</td>
                        <td>{float(r["الدفعات اللاحقة"]):,.2f}</td>
                        <td>{float(r["إجمالي المحصّل"]):,.2f}</td>
                        <td style="color:red;font-weight:bold;">{float(r["المستحق"]):,.2f}</td>
                    </tr>"""

                # صف الإجماليات
                total_contract = sum_df["قيمة العقد"].sum()
                total_vat = sum_df["ضريبة 15%"].sum()
                total_grand = sum_df["الإجمالي مع الضريبة"].sum()
                total_adv2 = sum_df["الدفعة المقدمة"].sum()
                total_pays2 = sum_df["الدفعات اللاحقة"].sum()
                total_coll = sum_df["إجمالي المحصّل"].sum()
                total_due = sum_df["المستحق"].sum()

                full_html = f"""
                <style>
                @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
                .print-table-wrapper {{
                    font-family: 'Cairo', sans-serif;
                    direction: rtl;
                    padding: 20px;
                }}
                .print-factory-header {{
                    text-align: center;
                    border-bottom: 3px solid #1E3A8A;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                }}
                .print-factory-header h2 {{ color: #1E3A8A; margin: 0; font-size: 20px; }}
                .print-factory-header p {{ color: #555; margin: 3px 0; font-size: 12px; }}
                .print-title {{ text-align: center; color: #1E3A8A; font-size: 16px; font-weight: bold; margin: 10px 0; }}
                .print-date {{ text-align: center; color: #666; font-size: 12px; margin-bottom: 15px; }}
                .main-table {{
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 11px;
                    direction: rtl;
                }}
                .main-table th {{
                    background: #1E3A8A;
                    color: white;
                    padding: 8px 5px;
                    text-align: center;
                    border: 1px solid #1E3A8A;
                    font-size: 11px;
                }}
                .main-table td {{
                    padding: 7px 5px;
                    text-align: center;
                    border: 1px solid #CBD5E1;
                    font-size: 11px;
                }}
                .main-table tr:nth-child(even) {{ background: #F8FAFC; }}
                .main-table tr:hover {{ background: #EFF6FF; }}
                .totals-row td {{
                    background: #1E3A8A !important;
                    color: white !important;
                    font-weight: bold;
                    padding: 8px 5px;
                    border: 1px solid #1E3A8A;
                }}
                .print-footer {{
                    margin-top: 20px;
                    text-align: center;
                    font-size: 11px;
                    color: #888;
                    border-top: 1px solid #CBD5E1;
                    padding-top: 8px;
                }}
                @media print {{
                    body {{ margin: 0; }}
                    .print-table-wrapper {{ padding: 10px; }}
                }}
                </style>

                <div class="print-table-wrapper">
                    <div class="print-factory-header">
                        <h2>{FACTORY_NAME}</h2>
                        <p>{FACTORY_ADDRESS}</p>
                        <p>س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p>
                    </div>
                    <div class="print-title">تقرير الطلبيات الجارية وحالتها المالية والتشغيلية</div>
                    <div class="print-date">تاريخ التقرير: {today_str} | عدد الطلبيات: {len(sum_df)}</div>

                    <table class="main-table">
                        <thead>
                            <tr>
                                <th>رقم الطلبية</th>
                                <th>العميل</th>
                                <th>الكمية المطلوبة</th>
                                <th>المصنّع</th>
                                <th>المسلّم</th>
                                <th>قيمة العقد (ر)</th>
                                <th>ضريبة 15% (ر)</th>
                                <th>الإجمالي مع الضريبة (ر)</th>
                                <th>الدفعة المقدمة (ر)</th>
                                <th>الدفعات اللاحقة (ر)</th>
                                <th>إجمالي المحصّل (ر)</th>
                                <th>🔴 المستحق (ر)</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rows_html}
                        </tbody>
                        <tfoot>
                            <tr class="totals-row">
                                <td colspan="5">الإجماليات الكلية</td>
                                <td>{total_contract:,.2f}</td>
                                <td>{total_vat:,.2f}</td>
                                <td>{total_grand:,.2f}</td>
                                <td>{total_adv2:,.2f}</td>
                                <td>{total_pays2:,.2f}</td>
                                <td>{total_coll:,.2f}</td>
                                <td>{total_due:,.2f}</td>
                            </tr>
                        </tfoot>
                    </table>
                    <div class="print-footer">
                        تم إنشاء هذا التقرير بواسطة نظام ERP — {FACTORY_NAME} — {today_str}
                    </div>
                </div>
                """

                # عرض الجدول في Streamlit
                st.dataframe(sum_df, use_container_width=True, hide_index=True)

                # زر تنزيل CSV
                st.download_button(
                    "⬇️ تنزيل CSV",
                    df_to_csv(sum_df),
                    "active_orders_summary.csv",
                    "text/csv"
                )

                # إضافة charset للـ HTML عشان العربي يظهر صح
                full_html_with_charset = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body>
""" + full_html + """
</body>
</html>"""

                st.download_button(
                    label="🖨️ تنزيل التقرير للطباعة (HTML)",
                    data=full_html_with_charset.encode('utf-8'),
                    file_name="orders_report.html",
                    mime="text/html; charset=utf-8",
                    help="افتح الملف في المتصفح ثم اضغط Cmd+P للطباعة أو حفظ PDF"
                )
                st.caption("💡 بعد التنزيل: افتح الملف في Safari أو Chrome ثم اضغط Cmd+P لطباعته أو حفظه PDF")

    # تبويب 4: دفعات عميل
    with tabs[3]:
        if 'pk'  not in st.session_state: st.session_state.pk  = 0
        if 'cust_rcpt_html'  not in st.session_state: st.session_state.cust_rcpt_html  = None
        if 'cust_rcpt_ready' not in st.session_state: st.session_state.cust_rcpt_ready = False
        pk = st.session_state.pk
        cdf2 = run_query("SELECT id,trade_name,cr_number,tax_number FROM customers ORDER BY trade_name")
        if not cdf2.empty:
            sc   = st.selectbox("العميل:", cdf2['trade_name'].tolist(), key=f"pay_cust_{pk}")
            cid2 = int(cdf2[cdf2['trade_name']==sc]['id'].iloc[0])
            cust_row_p = cdf2[cdf2['trade_name']==sc].iloc[0]
            odf2 = run_query("""SELECT o.order_id, o.total_price*1.15 as grand_vat,
                COALESCE(o.advance_paid,0) as adv,
                COALESCE((SELECT SUM(amount) FROM customer_payments WHERE order_id=o.order_id),0) as paid_so_far
                FROM orders o WHERE o.customer_id=:c AND o.status='قيد التنفيذ'""",{"c":cid2})
            if odf2.empty:
                st.info("لا توجد طلبيات جارية لهذا العميل.")
            else:
                odf2['المستحق'] = odf2['grand_vat'] - odf2['adv'] - odf2['paid_so_far']
                ord_opts = [f"{r['order_id']} | مستحق: {float(r['المستحق']):,.0f} ر" for _,r in odf2.iterrows()]
                so_sel = st.selectbox("الطلبية:", ord_opts, key=f"pay_ord_{pk}")
                so_idx = ord_opts.index(so_sel)
                so = odf2.iloc[so_idx]['order_id']
                ord_due    = float(odf2.iloc[so_idx]['المستحق'])
                ord_grand  = float(odf2.iloc[so_idx]['grand_vat'])
                ord_adv    = float(odf2.iloc[so_idx]['adv'])
                ord_paid   = float(odf2.iloc[so_idx]['paid_so_far'])

                pc1,pc2,pc3 = st.columns(3)
                pc1.metric("إجمالي الطلبية (مع الضريبة)", f"{ord_grand:,.2f} ر")
                pc2.metric("المدفوع سابقاً", f"{ord_paid + ord_adv:,.2f} ر")

                if ord_due <= 0.5:
                    pc3.metric("المستحق", "مسدد ✅")
                    st.error("⛔ لا توجد مبالغ مستحقة على هذه الطلبية — الرجاء اختيار طلبية أخرى.")
                else:
                    pc3.metric("🔴 المستحق", f"{ord_due:,.2f} ر")
                    _max_cust = round(float(ord_due), 2)
                    pa  = st.number_input(f"مبلغ الدفعة (ريال) — الحد الأقصى: {_max_cust:,.2f} ر:",
                                          min_value=0.01, max_value=_max_cust, value=_max_cust,
                                          key=f"pay_amt_{pk}")
                    pt  = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"], key=f"pay_pt_{pk}")
                    pb  = st.text_input("البنك / رقم الحوالة:", key=f"pay_bank_{pk}")

                    if st.button("💵 اعتماد الدفعة وإصدار الإيصال", type="primary", key=f"pay_btn_{pk}"):
                        # تحقق نهائي من المستحق الفعلي
                        _live_paid_c = float(run_query(
                            "SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE order_id=:oid",
                            {"oid":so})['t'].iloc[0])
                        _live_due_c  = ord_grand - ord_adv - _live_paid_c
                        if pa > _live_due_c + 0.01:
                            st.error(f"⛔ المبلغ ({pa:,.2f} ر) يتجاوز المستحق الفعلي ({_live_due_c:,.2f} ر)")
                        else:
                            ok_cp = run_write(
                                "INSERT INTO customer_payments(customer_id,order_id,amount,payment_type,bank_name) VALUES(:ci,:oi,:a,:pt,:b)",
                                {"ci":int(cid2),"oi":str(so),"a":float(round(pa,2)),"pt":str(pt),"b":str(pb or "")})
                            if ok_cp:
                                new_due_c = max(0, _live_due_c - pa)
                                today_cr  = datetime.date.today().strftime("%Y/%m/%d")
                                rcpt_no_c = f"CPR-{so}-{datetime.date.today().strftime('%Y%m%d')}-{pk+1}"
                                _qr_cp_b64 = make_qr_b64(
                                    f"=== إيصال دفعة عميل ===\nرقم الإيصال: {rcpt_no_c}\nالعميل: {sc}\nرقم الطلبية: {so}\nالمبلغ: {pa:.2f} ريال\nتاريخ الدفع: {today_cr}",
                                    color=(30,58,138), module_size=6)
                                due_c_color = "#16a34a" if new_due_c <= 0.5 else "#dc2626"
                                cust_rcpt = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:28px;max-width:750px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #16a34a;padding-bottom:12px;margin-bottom:16px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;margin-bottom:3px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.hdr-right{{text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:6px;}}
.badge{{background:#16a34a;color:#fff;padding:6px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
.badge-en{{background:#f0fdf4;color:#16a34a;padding:3px 12px;border-radius:8px;font-size:11px;font-weight:700;border:1px solid #16a34a;direction:ltr;}}
.qr-img{{width:70px;height:70px;border:2px solid #16a34a;border-radius:6px;}}
.amt-box{{background:linear-gradient(135deg,#16a34a,#15803d);color:#fff;border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin:14px 0;}}
.amt-box .lbl{{font-size:13px;opacity:.85;}} .amt-box .lbl-en{{font-size:10px;opacity:.6;direction:ltr;}} .amt-box .val{{font-size:26px;font-weight:800;}}
.grid2{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px;}}
.ig{{background:#f8fafc;border-radius:8px;padding:10px;border-right:3px solid #16a34a;}}
.ig .lbl{{font-size:10px;color:#94a3b8;margin-bottom:3px;}} .ig .val{{font-size:12px;font-weight:700;}}
.bal{{background:#f1f5f9;border-radius:10px;padding:12px 16px;margin-bottom:14px;}}
.bal h4{{color:#1E3A8A;font-size:12px;margin-bottom:8px;border-bottom:1px solid #e2e8f0;padding-bottom:5px;}}
.brow{{display:flex;justify-content:space-between;font-size:12px;padding:4px 0;}}
.brow.total{{font-weight:700;font-size:13px;border-top:1px solid #e2e8f0;margin-top:4px;padding-top:6px;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:32px;gap:14px;}}
.sig-box{{text-align:center;flex:1;}} .sig-line{{border-top:2px solid #1e293b;margin-bottom:6px;height:34px;}}
.sig-ar{{font-size:11px;font-weight:700;}} .sig-en{{font-size:10px;color:#64748b;}}
.footer{{margin-top:18px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;max-width:100%;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:28px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>الرقم الضريبي: {FACTORY_TAX}</p><p style="margin-top:5px;">رقم الإيصال: <b>{rcpt_no_c}</b> | {today_cr}</p></div>
  <div class="hdr-right"><div class="badge">إيصال دفعة عميل</div><div class="badge-en">Customer Payment Receipt</div><img class="qr-img" src="data:image/png;base64,{_qr_cp_b64}" alt="QR"></div>
</div>
<div class="amt-box">
  <div><div class="lbl">المبلغ المستلم</div><div class="lbl-en">Amount Received</div></div>
  <div class="val">{pa:,.2f} ريال</div>
</div>
<div class="grid2">
  <div class="ig"><div class="lbl">العميل / Customer</div><div class="val">{sc}</div></div>
  <div class="ig"><div class="lbl">رقم الطلبية / Order No.</div><div class="val">{so}</div></div>
  <div class="ig"><div class="lbl">طريقة الدفع / Method</div><div class="val">{pt}</div></div>
  <div class="ig"><div class="lbl">البنك / Bank</div><div class="val">{pb or "—"}</div></div>
  <div class="ig"><div class="lbl">التاريخ / Date</div><div class="val">{today_cr}</div></div>
  <div class="ig"><div class="lbl">رقم الإيصال</div><div class="val">{rcpt_no_c}</div></div>
</div>
<div class="bal">
  <h4>📊 ملخص حساب الطلبية</h4>
  <div class="brow"><span>إجمالي الطلبية (مع الضريبة)</span><span>{ord_grand:,.2f} ر</span></div>
  <div class="brow"><span>الدفعة المقدمة</span><span>{ord_adv:,.2f} ر</span></div>
  <div class="brow"><span>المدفوع سابقاً</span><span>{ord_paid:,.2f} ر</span></div>
  <div class="brow"><span>هذه الدفعة</span><span style="color:#16a34a;font-weight:700;">{pa:,.2f} ر</span></div>
  <div class="brow total"><span>الرصيد المتبقي</span><span style="color:{due_c_color};">{new_due_c:,.2f} ر {"✅ مسدد" if new_due_c<=0.5 else ""}</span></div>
</div>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع المحاسب</div><div class="sig-en">Accountant</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع العميل</div><div class="sig-en">Customer</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">ختم الشركة</div><div class="sig-en">Stamp</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_cr}</span></div>
</body></html>"""
                                st.session_state.cust_rcpt_html  = cust_rcpt
                                st.session_state.cust_rcpt_ready = True
                                st.success(f"✅ تم تسجيل {pa:,.2f} ريال | متبقي: {new_due_c:,.2f} ريال")
                                st.session_state.pk += 1

            if st.session_state.cust_rcpt_ready and st.session_state.cust_rcpt_html:
                st.download_button("🖨️ طباعة الإيصال (HTML)",
                    st.session_state.cust_rcpt_html.encode('utf-8'),
                    f"CustReceipt_{st.session_state.pk}.html",
                    "text/html; charset=utf-8", key="dl_cust_rcpt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")
                if st.button("🆕 دفعة جديدة", key="new_cust_pmt"):
                    st.session_state.cust_rcpt_ready = False
                    st.session_state.cust_rcpt_html  = None
                    st.rerun()

    # تبويب 5: كشف حساب عميل التفصيلي
    with tabs[4]:
        cdf3 = run_query("SELECT id,trade_name,cr_number,tax_number FROM customers ORDER BY trade_name")
        if not cdf3.empty:
            sel_c3 = st.selectbox("اختر العميل:", cdf3['trade_name'].tolist(), key="sc3")
            cid3 = int(cdf3[cdf3['trade_name']==sel_c3]['id'].iloc[0])
            cust_row3 = cdf3[cdf3['trade_name']==sel_c3].iloc[0]
            cust_info3 = {
                'cr_number':  str(cust_row3.get('cr_number','') or '—'),
                'tax_number': str(cust_row3.get('tax_number','') or '—'),
            }
            d1,d2 = st.columns(2)
            ds = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="sds")
            de = d2.date_input("إلى:", datetime.date.today(), key="sde")
            if st.button("📊 عرض كشف الحساب"):
                # جلب بيانات شاملة لكل طلبية
                orders_stmt = run_query("""SELECT o.order_id, o.order_date, o.qty,
                    o.unit_price, o.total_price, o.advance_paid, o.status,
                    o.tank_use, o.tank_capacity, o.tank_type
                    FROM orders o WHERE o.customer_id=:cid AND o.order_date BETWEEN :s AND :e
                    ORDER BY o.order_date""", {"cid":cid3,"s":ds,"e":de})
                if orders_stmt.empty:
                    st.info("لا توجد طلبيات في هذه الفترة.")
                else:
                    # ---- جمع بيانات كل طلبية ----
                    # ---- بناء صفوف كشف الحساب ----
                    today_cst = datetime.date.today().strftime("%Y/%m/%d")
                    cust_cr  = str(cust_row3.get('cr_number','') or '—')
                    cust_tax = str(cust_row3.get('tax_number','') or '—')
                    cust_phone = str(cust_row3.get('phone','') or '—')
                    cust_addr  = str(cust_row3.get('address','') or '—')

                    stmt_rows  = []
                    html_rows  = ""
                    g_contract = 0.0; g_adv = 0.0; g_paid = 0.0; g_del = 0; g_qty = 0

                    for _, ord_row in orders_stmt.iterrows():
                        oid_s        = ord_row['order_id']
                        qty_total    = int(ord_row['qty'])
                        unit_p       = float(ord_row['unit_price'])
                        contract     = float(ord_row['total_price'])
                        contract_vat = round(contract * 1.15, 2)
                        adv          = float(ord_row['advance_paid'])

                        # دفعات العميل كلها
                        pays = run_query(
                            "SELECT payment_date,amount FROM customer_payments WHERE order_id=:oid AND customer_id=:cid ORDER BY payment_date",
                            {"oid":oid_s,"cid":cid3})
                        total_paid   = float(pays['amount'].sum()) if not pays.empty else 0.0
                        pays_list    = pays.to_dict('records') if not pays.empty else []

                        # التسليمات
                        dels = run_query(
                            "SELECT delivery_date,shipped_qty FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_date",
                            {"oid":oid_s})
                        total_del   = int(dels['shipped_qty'].sum()) if not dels.empty else 0
                        del_date    = str(dels['delivery_date'].iloc[-1]) if not dels.empty else "—"
                        delivered_val     = round(total_del * unit_p * 1.15, 2)
                        remaining_qty     = qty_total - total_del
                        remaining_val_del = round(remaining_qty * unit_p * 1.15, 2)
                        remaining_contract= max(0, round(contract_vat - adv - total_paid, 2))

                        g_contract += contract_vat
                        g_adv      += adv
                        g_paid     += total_paid
                        g_del      += total_del
                        g_qty      += qty_total

                        # ---- سطر للطلبية نفسها ----
                        stmt_rows.append({
                            "النوع":                   "📦 طلبية",
                            "رقم الطلبية":             oid_s,
                            "التاريخ":                 str(ord_row['order_date']),
                            "البيان":                  f"إجمالي العقد شامل الضريبة",
                            "المبلغ (ريال)":           f"{contract_vat:,.2f}",
                            "عدد الخزانات الكلي":      qty_total,
                            "المورّد حتى الآن":         total_del,
                            "قيمة الموردة":            f"{delivered_val:,.2f}",
                            "خزانات متبقية":           remaining_qty,
                            "قيمة المتبقية":           f"{remaining_val_del:,.2f}",
                            "متبقي من العقد":          f"{remaining_contract:,.2f}",
                        })
                        # سطر الدفعة المقدمة
                        stmt_rows.append({
                            "النوع":                   "💰 مقدم",
                            "رقم الطلبية":             oid_s,
                            "التاريخ":                 str(ord_row['order_date']),
                            "البيان":                  "دفعة مقدمة",
                            "المبلغ (ريال)":           f"{adv:,.2f}",
                            "عدد الخزانات الكلي":      "—",
                            "المورّد حتى الآن":         "—",
                            "قيمة الموردة":            "—",
                            "خزانات متبقية":           "—",
                            "قيمة المتبقية":           "—",
                            "متبقي من العقد":          "—",
                        })
                        # سطر لكل دفعة
                        running_balance = contract_vat - adv
                        for pay in pays_list:
                            running_balance = max(0, running_balance - float(pay['amount']))
                            stmt_rows.append({
                                "النوع":               "💵 دفعة",
                                "رقم الطلبية":         oid_s,
                                "التاريخ":             str(pay['payment_date']),
                                "البيان":              "دفعة مستلمة",
                                "المبلغ (ريال)":       f"{float(pay['amount']):,.2f}",
                                "عدد الخزانات الكلي":  "—",
                                "المورّد حتى الآن":     total_del,
                                "قيمة الموردة":        f"{delivered_val:,.2f}",
                                "خزانات متبقية":       remaining_qty,
                                "قيمة المتبقية":       f"{remaining_val_del:,.2f}",
                                "متبقي من العقد":      f"{running_balance:,.2f}",
                            })

                        # ---- صفوف HTML — صف لكل دفعة ----
                        # صف الطلبية
                        html_rows += f"""<tr style="background:#eff6ff;">
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;font-weight:700;color:#1E3A8A;">📦 {oid_s}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{ord_row['order_date']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">إجمالي العقد</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;">{contract_vat:,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{qty_total}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;">{total_del}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{delivered_val:,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{remaining_qty}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{remaining_val_del:,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{remaining_contract:,.2f}</td>
                        </tr>"""
                        # صف المقدم
                        html_rows += f"""<tr style="background:#f0fdf4;">
                          <td style="padding:7px 10px;border:1px solid #e2e8f0;color:#16a34a;">💰 مقدم</td>
                          <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{ord_row['order_date']}</td>
                          <td style="padding:7px 10px;border:1px solid #e2e8f0;">دفعة مقدمة</td>
                          <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;font-weight:700;">{adv:,.2f}</td>
                          <td colspan="6" style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#94a3b8;">—</td>
                        </tr>"""
                        # صف لكل دفعة
                        rb2 = contract_vat - adv
                        for pay in pays_list:
                            rb2 = max(0, rb2 - float(pay['amount']))
                            html_rows += f"""<tr>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;color:#1E3A8A;">💵 دفعة</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{pay['payment_date']}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;">دفعة مستلمة</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;font-weight:700;">{float(pay['amount']):,.2f}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">—</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;">{total_del}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{delivered_val:,.2f}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{remaining_qty}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{remaining_val_del:,.2f}</td>
                              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{rb2:,.2f}</td>
                            </tr>"""

                    # ---- عرض في Streamlit ----
                    g1,g2,g3,g4 = st.columns(4)
                    g1.metric("إجمالي قيمة العقود", f"{g_contract:,.2f} ر")
                    g2.metric("إجمالي المدفوع+المقدم", f"{g_adv+g_paid:,.2f} ر")
                    g3.metric("🔴 المستحق الإجمالي", f"{max(0,g_contract-g_adv-g_paid):,.2f} ر")
                    g4.metric("الخزانات المتبقية", f"{g_qty-g_del} من {g_qty}")

                    stmt_df = pd.DataFrame(stmt_rows)
                    st.dataframe(stmt_df, use_container_width=True, hide_index=True)

                    # ---- HTML للطباعة ----
                    bal_color_f = "#dc2626" if (g_contract-g_adv-g_paid)>0 else "#16a34a"
                    stmt_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:11px;padding:22px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:16px;}}
.hdr h1{{color:#1E3A8A;font-size:17px;font-weight:800;}} .hdr p{{color:#64748b;font-size:10px;margin:2px 0;}}
.badge{{background:#1E3A8A;color:#fff;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;}}
.cust-box{{background:linear-gradient(135deg,#1E3A8A,#2563eb);color:#fff;border-radius:10px;padding:14px 18px;margin-bottom:14px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;}}
.cust-box h2{{font-size:15px;margin-bottom:3px;}} .cust-box p{{font-size:10px;opacity:.85;}}
.summary{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px;}}
.sc{{background:#f1f5f9;border-radius:8px;padding:10px;text-align:center;border-top:3px solid #1E3A8A;}}
.sc.red{{border-top-color:#dc2626;background:#fef2f2;}} .sc .lbl{{font-size:9px;color:#94a3b8;}} .sc .val{{font-size:14px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;margin-bottom:12px;font-size:10px;}}
thead th{{background:#1E3A8A;color:#fff;padding:8px 6px;text-align:center;white-space:nowrap;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
tfoot td{{background:#1E3A8A;color:#fff;font-weight:700;padding:8px 6px;text-align:center;}}
.final{{background:#1E3A8A;color:#fff;border-radius:10px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;margin-top:14px;}}
.final .lbl{{font-size:12px;opacity:.85;}} .final .amt{{font-size:22px;font-weight:800;}}
.footer{{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;}}
@media print{{body{{padding:12px;font-size:10px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:24px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>الرقم الضريبي: {FACTORY_TAX}</p></div>
  <div style="text-align:left;"><div class="badge">كشف حساب عميل</div><p style="color:#64748b;font-size:10px;margin-top:6px;">الفترة: {ds} — {de}</p><p style="color:#64748b;font-size:10px;">{today_cst}</p></div>
</div>
<div class="cust-box">
  <div><h2>👤 {sel_c3}</h2><p>س.ت: {cust_cr} | الرقم الضريبي: {cust_tax}</p></div>
  <div style="text-align:left;font-size:10px;"><p>عدد الطلبيات: {len(orders_stmt)}</p><p>الفترة: {ds} — {de}</p></div>
</div>
<div class="summary">
  <div class="sc"><div class="lbl">إجمالي قيمة العقود</div><div class="val">{g_contract:,.2f} ر</div></div>
  <div class="sc"><div class="lbl">إجمالي المدفوع والمقدم</div><div class="val">{g_adv+g_paid:,.2f} ر</div></div>
  <div class="sc red"><div class="lbl">المستحق الإجمالي</div><div class="val" style="color:#dc2626;">{max(0,g_contract-g_adv-g_paid):,.2f} ر</div></div>
  <div class="sc"><div class="lbl">الخزانات المتبقية</div><div class="val">{g_qty-g_del} / {g_qty}</div></div>
</div>
<table>
  <thead><tr>
    <th>النوع</th><th>التاريخ</th><th>البيان</th><th>المبلغ (ريال)</th>
    <th>عدد الخزانات الكلي</th><th>المورّد حتى الآن</th>
    <th>قيمة الموردة</th><th>خزانات متبقية</th>
    <th>قيمة المتبقية</th><th>المستحق من العقد</th>
  </tr></thead>
  <tbody>{html_rows}</tbody>
  <tfoot><tr>
    <td colspan="3" style="padding:9px;">الإجماليات</td>
    <td style="padding:9px;text-align:center;">{g_contract+g_adv+g_paid:,.2f}</td>
    <td style="padding:9px;text-align:center;">{g_qty}</td>
    <td style="padding:9px;text-align:center;">{g_del}</td>
    <td style="padding:9px;text-align:center;">{round(g_del*(g_contract/max(g_qty,1))/1.15*1.15,2):,.2f}</td>
    <td style="padding:9px;text-align:center;">{g_qty-g_del}</td>
    <td style="padding:9px;text-align:center;">—</td>
    <td style="padding:9px;text-align:center;">{max(0,g_contract-g_adv-g_paid):,.2f}</td>
  </tr></tfoot>
</table>
<div class="final">
  <div><div class="lbl">الرصيد الإجمالي المستحق</div><div style="font-size:10px;opacity:.7;">Total Outstanding Balance</div></div>
  <div class="amt">{max(0,g_contract-g_adv-g_paid):,.2f} ريال</div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_cst}</span></div>
</body></html>"""

                    st.markdown("---")
                    col_dl1, col_dl2 = st.columns(2)
                    col_dl1.download_button("⬇️ تنزيل CSV", df_to_csv(stmt_df), f"stmt_{sel_c3}_{datetime.date.today()}.csv", "text/csv")
                    col_dl2.download_button("🖨️ طباعة كشف الحساب (HTML)",
                        stmt_html.encode('utf-8'),
                        f"customer_statement_{sel_c3}_{datetime.date.today()}.html",
                        "text/html; charset=utf-8")
                    st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")

# ==========================================
# [3] التصنيع
# ==========================================
elif menu == "🏭 التصنيع":
    st.subheader("🏭 إدارة صالة الإنتاج")

    # --- session state للتصنيع ---
    if 'prod_stage' not in st.session_state: st.session_state.prod_stage = 'new'        # new | open | closing
    if 'prod_shift_id' not in st.session_state: st.session_state.prod_shift_id = None
    if 'prod_oid' not in st.session_state: st.session_state.prod_oid = None
    if 'prod_planned' not in st.session_state: st.session_state.prod_planned = 0
    if 'prod_calc' not in st.session_state: st.session_state.prod_calc = {}
    if 'prod_tank_actuals' not in st.session_state: st.session_state.prod_tank_actuals = {}
    if 'prod_tank_serials' not in st.session_state: st.session_state.prod_tank_serials = []
    if 'prod_supervisor' not in st.session_state: st.session_state.prod_supervisor = ''

    # نوع الراتنج يُحدَّد ديناميكياً حسب الطلبية
    _RESIN_OPTIONS = [
        "راتنج كميائي صنف اول للديزل",
        "راتنج كميائي صنف ٢ للصرف الصحي",
        "ريزن عادي"
    ]
    def _get_resin_type(oid):
        """يجلب نوع الراتنج من session_state فقط — العمود غير موجود في DB"""
        return st.session_state.get(f'resin_type_{oid}', _RESIN_OPTIONS[0])

    def _build_mat_map(resin_type):
        return {
            "راتنج":       resin_type,
            "ألياف Mat":   "ألياف (Mat 450)",
            "روفرز":       "روفرز (Roving 600)",
            "تيسو":        "تيسو (Tissue)",
            "مصلد":        "مصلد (Catalyst)",
            "كالسيوم":     "كربونات الكالسيوم",
            "سيليكا":      "سيليكا (Silica)",
        }

    MAT_MAP_KEYS = _build_mat_map(_RESIN_OPTIONS[0])  # افتراضي، سيُحدَّث عند اختيار الطلبية

    def make_dispatch_html(oid, order_row, calc_dict, planned_qty, shift_id, supervisor, title="أمر صرف مواد خام"):
        today_str = datetime.date.today().strftime("%Y/%m/%d")
        rows = ""
        total_items = len(calc_dict)
        for i,(mat,qty) in enumerate(calc_dict.items()):
            bg = "#f8fafc" if i%2==0 else "#fff"
            rows += f"""<tr style="background:{bg};">
                <td style="padding:9px 12px;border:1px solid #e2e8f0;">{mat}</td>
                <td style="padding:9px 12px;border:1px solid #e2e8f0;text-align:center;font-weight:700;">{qty:,.3f}</td>
                <td style="padding:9px 12px;border:1px solid #e2e8f0;text-align:center;">كجم / م²</td>
            </tr>"""
        return f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:14px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#1E3A8A;color:#fff;padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;}}
.info-box{{background:#f1f5f9;border-radius:10px;padding:14px 18px;margin-bottom:18px;display:flex;flex-wrap:wrap;gap:18px;}}
.info-item span{{display:block;}} .info-item .lbl{{font-size:10px;color:#94a3b8;}} .info-item .val{{font-size:13px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px 12px;text-align:center;font-size:12px;}}
.footer{{margin-top:30px;border-top:1px solid #e2e8f0;padding-top:12px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:40px;}}
.sig-box{{text-align:center;width:160px;}} .sig-line{{border-top:1px solid #94a3b8;margin-bottom:6px;}} .sig-lbl{{font-size:11px;color:#64748b;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:26px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p></div>
  <div style="text-align:left;"><div class="badge">{title}</div><p style="margin-top:8px;color:#64748b;font-size:11px;">التاريخ: {today_str}</p><p style="color:#64748b;font-size:11px;">رقم الوردية: #{shift_id}</p></div>
</div>
<div class="info-box">
  <div class="info-item"><span class="lbl">رقم الطلبية</span><span class="val">{oid}</span></div>
  <div class="info-item"><span class="lbl">عدد الخزانات المخططة</span><span class="val">{planned_qty} خزان</span></div>
  <div class="info-item"><span class="lbl">المشرف</span><span class="val">{supervisor or '—'}</span></div>
  <div class="info-item"><span class="lbl">تاريخ الوردية</span><span class="val">{today_str}</span></div>
</div>
<table><thead><tr><th>المادة الخام</th><th>الكمية المطلوبة</th><th>الوحدة</th></tr></thead><tbody>{rows}</tbody></table>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">أمين المخزن</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">المشرف</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl">مدير الإنتاج</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {today_str}</span></div>
</body></html>"""

    def make_comparison_html(oid, shift_id, supervisor, planned_qty, actual_qty, calc_dict, actual_totals, return_items, extra_items):
        today_str = datetime.date.today().strftime("%Y/%m/%d")
        rows = ""
        for mat, planned_q in calc_dict.items():
            actual_q = actual_totals.get(mat, 0.0)
            diff = actual_q - planned_q
            diff_color = "#dc2626" if diff > 0 else ("#16a34a" if diff < 0 else "#1e293b")
            diff_txt = f"+{diff:,.3f}" if diff > 0 else f"{diff:,.3f}"
            status = "زيادة استهلاك 🔴" if diff > 0 else ("وفر 🟢" if diff < 0 else "مطابق ✅")
            rows += f"""<tr>
              <td style="padding:8px 10px;border:1px solid #e2e8f0;">{mat}</td>
              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{planned_q:,.3f}</td>
              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{actual_q:,.3f}</td>
              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:{diff_color};font-weight:700;">{diff_txt}</td>
              <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{status}</td>
            </tr>"""
        ret_rows = ""
        for m,q in return_items.items():
            ret_rows += f'<tr><td style="padding:7px 10px;border:1px solid #e2e8f0;">{m}</td><td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;font-weight:700;">{q:,.3f}</td><td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">كجم/م²</td></tr>'
        ext_rows = ""
        for m,q in extra_items.items():
            ext_rows += f'<tr><td style="padding:7px 10px;border:1px solid #e2e8f0;">{m}</td><td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{q:,.3f}</td><td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">كجم/م²</td></tr>'
        return f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:14px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#d97706;color:#fff;padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;}}
.section-title{{font-size:13px;font-weight:700;color:#1E3A8A;border-right:4px solid #FBBF24;padding-right:10px;margin:18px 0 8px 0;}}
table{{width:100%;border-collapse:collapse;margin-bottom:14px;}}
thead th{{background:#1E3A8A;color:#fff;padding:9px 10px;text-align:center;font-size:12px;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:26px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
  <div style="text-align:left;"><div class="badge">تقرير مقارنة المواد — إنهاء الوردية</div><p style="margin-top:8px;color:#64748b;font-size:11px;">التاريخ: {today_str} | وردية: #{shift_id}</p><p style="color:#64748b;font-size:11px;">طلبية: {oid} | مشرف: {supervisor or '—'} | مخطط: {planned_qty} | فعلي: {actual_qty}</p></div>
</div>
<div class="section-title">📊 جدول المقارنة: المصروف مقابل المستهلك</div>
<table><thead><tr><th>المادة</th><th>المصروف (مخطط)</th><th>المستهلك (فعلي)</th><th>الفرق</th><th>الحالة</th></tr></thead><tbody>{rows}</tbody></table>
{"<div class='section-title' style='color:#16a34a;'>🟢 أمر ارتجاع للمخزن</div><table><thead><tr><th>المادة</th><th>الكمية المرتجعة</th><th>الوحدة</th></tr></thead><tbody>"+ret_rows+"</tbody></table>" if ret_rows else ""}
{"<div class='section-title' style='color:#dc2626;'>🔴 أمر صرف إضافي من المخزن</div><table><thead><tr><th>المادة</th><th>الكمية الإضافية</th><th>الوحدة</th></tr></thead><tbody>"+ext_rows+"</tbody></table>" if ext_rows else ""}
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {today_str}</span></div>
</body></html>"""

    odf = run_query("SELECT o.order_id,c.trade_name,o.qty,o.tank_use,o.tank_capacity,o.tank_type,o.resin_exp,o.mat_exp,o.roving_exp,o.tissue_exp,o.catalyst_exp,o.calcium_exp,o.silica_exp FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
    if odf.empty:
        st.info("لا توجد طلبيات جارية.")
    else:
        # ===== مرحلة 1: بدء وردية جديدة =====
        if st.session_state.prod_stage == 'new':
            st.markdown("### 🟢 بدء وردية جديدة")
            opts = [
                f"{r['order_id']} | {r['trade_name']} | {r['qty']} خزان | سعة: {str(r['tank_capacity'] or '—').strip() or '—'}"
                for _,r in odf.iterrows()]
            sel = st.selectbox("اختر الطلبية:", opts, key="prod_sel")
            oid = sel.split(" | ")[0]
            row = odf[odf['order_id']==oid].iloc[0]

            # ---- تحديد نوع الراتنج للطلبية المختارة ----
            _order_resin_type = _get_resin_type(oid)
            _resin_idx = _RESIN_OPTIONS.index(_order_resin_type) if _order_resin_type in _RESIN_OPTIONS else 0
            _resin_display = st.selectbox(
                "نوع الراتنج للطلبية:",
                _RESIN_OPTIONS,
                index=_resin_idx,
                key=f"prod_resin_{oid}",
                help="يُحدَّد من الطلبية — يمكن تغييره إذا لزم")
            # حفظ الاختيار
            st.session_state[f'resin_type_{oid}'] = _resin_display
            # إعادة بناء MAT_MAP_KEYS بنوع الراتنج الصحيح
            MAT_MAP_KEYS = _build_mat_map(_resin_display)

            # حساب الخزانات المتبقية للتصنيع
            _total_order_qty = int(row['qty'])
            _already_made = int(run_query(
                "SELECT COALESCE(SUM(actual_qty),0) as t FROM production_days WHERE order_id=:oid AND status='مغلق'",
                {"oid":oid})['t'].iloc[0])
            _remaining_to_make = max(0, _total_order_qty - _already_made)

            if _remaining_to_make == 0:
                st.error(f"⛔ تم تصنيع كامل الطلبية ({_total_order_qty} خزان) — لا يمكن فتح وردية جديدة لهذه الطلبية.")
            else:
                st.info(f"📊 الطلبية: {_total_order_qty} خزان | المصنّع: {_already_made} | **المتاح للتصنيع: {_remaining_to_make} خزان**")

            c1,c2 = st.columns(2)
            tanks_today = c1.number_input(
                f"عدد الخزانات المستهدفة اليوم (الحد الأقصى: {_remaining_to_make}):",
                min_value=1,
                max_value=max(1, _remaining_to_make),
                value=min(2, max(1, _remaining_to_make)),
                key="prod_planned_n",
                disabled=(_remaining_to_make == 0))
            supervisor_inp = c2.text_input("اسم المشرف:", key="prod_sup_inp")

            resin_p  = float(row['resin_exp'] or 0)
            mat_p    = float(row['mat_exp'] or 0)
            roving_p = float(row['roving_exp'] or 0)
            tissue_p = float(row['tissue_exp'] or 0)
            cat_p    = float(row['catalyst_exp'] or 0)
            cal_p    = float(row['calcium_exp'] or 0)
            sil_p    = float(row['silica_exp'] or 0)

            calc = {
                "راتنج":     tanks_today * resin_p,
                "ألياف Mat": tanks_today * mat_p,
                "روفرز":     tanks_today * roving_p,
                "تيسو":      tanks_today * tissue_p,
                "مصلد":      tanks_today * cat_p,
                "كالسيوم":   tanks_today * cal_p,
                "سيليكا":    tanks_today * sil_p,
            }

            st.markdown("#### 📋 أمر صرف المواد")
            disp_df = pd.DataFrame([{"المادة":k,"الكمية المطلوبة":f"{v:,.3f}","الوحدة":"كجم/م²"} for k,v in calc.items()])
            st.dataframe(disp_df, use_container_width=True, hide_index=True)

            dispatch_html = make_dispatch_html(oid, row, calc, tanks_today, "مؤقت", supervisor_inp)
            st.download_button("🖨️ طباعة أمر الصرف (HTML)", dispatch_html.encode('utf-8'), f"dispatch_{oid}_{datetime.date.today()}.html", "text/html; charset=utf-8", key="dl_dispatch_pre")
            st.caption("💡 افتح الملف في المتصفح ثم Ctrl+P للطباعة")

            # ========== فحص المخزن قبل بدء الوردية ==========
            # MAT_MAP_KEYS محدَّث بنوع الراتنج الصحيح أعلاه
            mat_map_full_chk = {MAT_MAP_KEYS[k]: v for k,v in calc.items() if v > 0}
            inv_chk = run_query("SELECT material_name,quantity FROM inventory")
            inv_chk_dict = {r['material_name']: float(r['quantity']) for _,r in inv_chk.iterrows()} if not inv_chk.empty else {}
            prod_shortages = {m:q for m,q in mat_map_full_chk.items() if q > 0 and inv_chk_dict.get(m,0) < q}

            if prod_shortages:
                st.error("⛔ لا يوجد مواد خام كافية لهذا المنتج!")
                chk_rows = []
                for mat, needed in mat_map_full_chk.items():
                    if needed <= 0: continue
                    stock = inv_chk_dict.get(mat, 0.0)
                    short = max(0.0, needed - stock)
                    chk_rows.append({"المادة":mat, "المخزون":f"{stock:,.3f}", "المطلوب":f"{needed:,.3f}", "العجز":f"{short:,.3f}", "الحالة":"🔴 عجز" if short>0 else "✅"})
                st.dataframe(pd.DataFrame(chk_rows), use_container_width=True, hide_index=True)

                # HTML تقرير النواقص
                today_po2 = datetime.date.today().strftime("%Y/%m/%d")
                short_rows_html = "".join(
                    f'<tr style="background:{"#fef2f2" if float(r["العجز"].replace(",",""))>0 else "#f0fdf4"};">'
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;">{r["المادة"]}</td>'
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r["المخزون"]}</td>'
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r["المطلوب"]}</td>'
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{r["العجز"]}</td>'
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r["الحالة"]}</td></tr>'
                    for r in chk_rows)
                shortage_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}} body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #dc2626;padding-bottom:14px;margin-bottom:20px;}}
.hdr h1{{color:#dc2626;font-size:18px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#dc2626;color:#fff;padding:6px 18px;border-radius:20px;font-size:14px;font-weight:700;}}
.warn-box{{background:#fef2f2;border-radius:10px;padding:14px;margin-bottom:18px;border-right:4px solid #dc2626;}}
table{{width:100%;border-collapse:collapse;margin-bottom:18px;}}
thead th{{background:#dc2626;color:#fff;padding:9px 10px;text-align:center;font-size:12px;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:26px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
  <div style="text-align:left;"><div class="badge">تقرير عجز المواد الخام</div><p style="margin-top:8px;color:#64748b;font-size:11px;">التاريخ: {today_po2}</p><p style="color:#64748b;font-size:11px;">الطلبية: {oid} | {tanks_today} خزان</p></div>
</div>
<div class="warn-box">
  <p><b>⚠️ تنبيه:</b> المخزن لا يحتوي على كميات كافية لتصنيع {tanks_today} خزان من الطلبية {oid}</p>
  <p>يرجى توفير المواد الناقصة قبل بدء الوردية.</p>
</div>
<table>
  <thead><tr><th>المادة الخام</th><th>المخزون الحالي</th><th>المطلوب للوردية</th><th>العجز</th><th>الحالة</th></tr></thead>
  <tbody>{short_rows_html}</tbody>
</table>
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {today_po2}</span></div>
</body></html>"""
                st.download_button("🖨️ طباعة تقرير العجز (HTML)", shortage_html.encode('utf-8'),
                    f"shortage_{oid}_{datetime.date.today()}.html", "text/html; charset=utf-8",
                    key="dl_shortage")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")
            else:
                st.success("✅ المخزن كافٍ — يمكن بدء الوردية")

            if st.button("🎬 بدء الوردية وصرف المواد من المخزن", type="primary", disabled=(_remaining_to_make == 0)):
                if not supervisor_inp:
                    st.error("أدخل اسم المشرف!")
                elif tanks_today > _remaining_to_make:
                    st.error(f"⛔ لا يمكن إنتاج {tanks_today} خزان — المتبقي للتصنيع هو {_remaining_to_make} خزان فقط")
                elif prod_shortages:
                    st.error("⛔ لا يمكن بدء الوردية — يوجد عجز في المواد الخام. أضف المواد أولاً.")
                else:
                    mat_map_full = {MAT_MAP_KEYS[k]: v for k,v in calc.items()}
                    for mat, qty in mat_map_full.items():
                        if qty > 0:
                            run_write(
                                """INSERT INTO inventory(material_name,quantity) VALUES(:m,0)
                                   ON CONFLICT(material_name) DO NOTHING""", {"m":mat})
                            run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m", {"q":float(qty),"m":str(mat)})
                    ok_s = run_write("INSERT INTO production_days(order_id,planned_qty,date) VALUES(:oid,:pq,:d)", {"oid":oid,"pq":tanks_today,"d":datetime.date.today()})
                    if ok_s:
                        sid_row = run_query("SELECT id FROM production_days WHERE order_id=:oid ORDER BY id DESC LIMIT 1", {"oid":oid})
                        sid = int(sid_row['id'].iloc[0])
                        st.session_state.prod_stage = 'open'
                        st.session_state.prod_shift_id = sid
                        st.session_state.prod_oid = oid
                        st.session_state.prod_planned = tanks_today
                        st.session_state.prod_calc = calc
                        st.session_state.prod_supervisor = supervisor_inp
                        st.session_state.prod_tank_actuals = {}
                        st.session_state.prod_tank_serials = []
                        st.success(f"✅ تم فتح الوردية #{sid} وصرف المواد!")
                        st.rerun()

        # ===== مرحلة 2: الوردية مفتوحة - إنهاء الوردية =====
        elif st.session_state.prod_stage == 'open':
            sid       = st.session_state.prod_shift_id
            oid       = st.session_state.prod_oid
            planned   = st.session_state.prod_planned
            calc      = st.session_state.prod_calc
            supervisor= st.session_state.prod_supervisor
            row       = odf[odf['order_id']==oid].iloc[0] if oid in odf['order_id'].values else odf.iloc[0]
            # تحديث MAT_MAP_KEYS بنوع الراتنج الصحيح
            _open_resin = st.session_state.get(f'resin_type_{oid}', _RESIN_OPTIONS[0])
            MAT_MAP_KEYS = _build_mat_map(_open_resin)

            st.info(f"🟡 الوردية #{sid} مفتوحة | الطلبية: **{oid}** | مخطط: **{planned}** خزان | مشرف: **{supervisor}**")

            # طباعة أمر الصرف الرسمي
            dispatch_html = make_dispatch_html(oid, row, calc, planned, sid, supervisor)
            st.download_button("🖨️ طباعة أمر الصرف الرسمي (HTML)", dispatch_html.encode('utf-8'), f"dispatch_{oid}_shift{sid}.html", "text/html; charset=utf-8", key="dl_dispatch_official")
            st.markdown("---")

            st.markdown("### 🔒 إنهاء الوردية — إدخال الاستهلاك الفعلي خزان بخزان")

            actual_qty_inp = st.number_input("عدد الخزانات المنتجة فعلياً:", min_value=1, value=planned, key="actual_qty_inp")

            st.markdown("#### أدخل الاستهلاك الفعلي لكل خزان:")
            tank_actuals = {}
            cols_tanks = st.columns(min(actual_qty_inp, 3))
            for i in range(1, actual_qty_inp+1):
                col = cols_tanks[(i-1) % min(actual_qty_inp, 3)]
                with col:
                    st.markdown(f"**خزان {i}**")
                    t_data = {}
                    t_data['راتنج']     = st.number_input(f"راتنج {i} (كجم):",    min_value=0.0, value=float(row['resin_exp'] or 0),    key=f"t_res_{i}")
                    t_data['ألياف Mat'] = st.number_input(f"ألياف Mat {i} (كجم):", min_value=0.0, value=float(row['mat_exp'] or 0),     key=f"t_mat_{i}")
                    t_data['روفرز']     = st.number_input(f"روفرز {i} (كجم):",    min_value=0.0, value=float(row['roving_exp'] or 0),   key=f"t_rov_{i}")
                    t_data['تيسو']      = st.number_input(f"تيسو {i} (م²):",       min_value=0.0, value=float(row['tissue_exp'] or 0),  key=f"t_tis_{i}")
                    t_data['مصلد']      = st.number_input(f"مصلد {i} (كجم):",     min_value=0.0, value=float(row['catalyst_exp'] or 0),key=f"t_cat_{i}")
                    t_data['كالسيوم']   = st.number_input(f"كالسيوم {i} (كجم):",  min_value=0.0, value=float(row['calcium_exp'] or 0), key=f"t_cal_{i}")
                    t_data['سيليكا']    = st.number_input(f"سيليكا {i} (كجم):",   min_value=0.0, value=float(row['silica_exp'] or 0),  key=f"t_sil_{i}")
                    tank_actuals[i] = t_data

            if st.button("✅ حساب المقارنة وإنهاء الوردية", type="primary"):
                # حساب الإجمالي الفعلي
                actual_totals = {mat: sum(tank_actuals[i].get(mat,0) for i in range(1,actual_qty_inp+1)) for mat in calc.keys()}

                # تحديد الفروق
                return_items = {}
                extra_items  = {}
                for mat, planned_q in calc.items():
                    actual_q = actual_totals.get(mat, 0.0)
                    diff = actual_q - planned_q
                    if diff < -0.001:   # وفر → ارتجاع للمخزن
                        return_items[mat] = abs(diff)
                    elif diff > 0.001:  # زيادة → صرف إضافي
                        extra_items[mat] = diff

                # تنفيذ الارتجاع
                inv_mat_map = {v:k for k,v in MAT_MAP_KEYS.items()}
                for mat_short, qty in return_items.items():
                    mat_full = MAT_MAP_KEYS.get(mat_short, mat_short)
                    run_write(
                        """INSERT INTO inventory(material_name,quantity) VALUES(:m,0)
                           ON CONFLICT(material_name) DO NOTHING""", {"m":str(mat_full)})
                    run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name=:m", {"q":float(qty),"m":str(mat_full)})

                # تنفيذ الصرف الإضافي
                for mat_short, qty in extra_items.items():
                    mat_full = MAT_MAP_KEYS.get(mat_short, mat_short)
                    run_write(
                        """INSERT INTO inventory(material_name,quantity) VALUES(:m,0)
                           ON CONFLICT(material_name) DO NOTHING""", {"m":str(mat_full)})
                    run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m", {"q":float(qty),"m":str(mat_full)})

                # إغلاق الوردية وإنشاء الأرقام التسلسلية
                run_write("UPDATE production_days SET actual_qty=:aq,status='مغلق' WHERE id=:sid", {"aq":actual_qty_inp,"sid":sid})
                serials = []
                for i in range(1, actual_qty_inp+1):
                    sn = f"SUBUL-SN-{datetime.date.today().year}-{random.randint(10000,99999)}-{i:02d}"
                    run_write("INSERT INTO production_tanks(serial_number,order_id,shift_id,prod_date,supervisor) VALUES(:sn,:oid,:sid,:pd,:sup)",
                              {"sn":sn,"oid":oid,"sid":sid,"pd":datetime.date.today(),"sup":supervisor})
                    serials.append(sn)

                # حفظ النتائج في session state للعرض
                st.session_state.prod_stage         = 'closing'
                st.session_state.prod_tank_actuals  = actual_totals
                st.session_state.prod_tank_serials  = serials
                st.session_state._return_items      = return_items
                st.session_state._extra_items       = extra_items
                st.session_state._actual_qty_done   = actual_qty_inp
                st.rerun()

        # ===== مرحلة 3: عرض النتائج + أوامر HTML + بدء جديد =====
        elif st.session_state.prod_stage == 'closing':
            sid            = st.session_state.prod_shift_id
            oid            = st.session_state.prod_oid
            planned        = st.session_state.prod_planned
            calc           = st.session_state.prod_calc
            supervisor     = st.session_state.prod_supervisor
            actual_totals  = st.session_state.prod_tank_actuals
            serials        = st.session_state.prod_tank_serials
            return_items   = st.session_state.get('_return_items', {})
            extra_items    = st.session_state.get('_extra_items', {})
            actual_qty_done= st.session_state.get('_actual_qty_done', planned)
            row            = odf[odf['order_id']==oid].iloc[0] if oid in odf['order_id'].values else odf.iloc[0]
            # تحديث MAT_MAP_KEYS بنوع الراتنج الصحيح من session_state
            _closing_resin = st.session_state.get(f'resin_type_{oid}', _RESIN_OPTIONS[0])
            MAT_MAP_KEYS   = _build_mat_map(_closing_resin)

            st.success(f"✅ تم إغلاق الوردية #{sid} بنجاح — {actual_qty_done} خزان")

            # الأرقام التسلسلية
            st.markdown("#### 🔢 الأرقام التسلسلية للخزانات المنتجة")
            sn_cols = st.columns(3)
            for i,sn in enumerate(serials):
                sn_cols[i%3].code(sn)

            # جدول المقارنة
            st.markdown("#### 📊 جدول مقارنة المواد")
            cmp_rows = []
            for mat, planned_q in calc.items():
                actual_q = actual_totals.get(mat, 0.0)
                diff = actual_q - planned_q
                cmp_rows.append({"المادة":mat,"المصروف":f"{planned_q:,.3f}","المستهلك":f"{actual_q:,.3f}","الفرق":f"{diff:+.3f}","الحالة":"زيادة 🔴" if diff>0.001 else ("وفر 🟢" if diff<-0.001 else "✅")})
            st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)

            if return_items:
                st.success(f"🟢 تم ارتجاع {len(return_items)} مادة للمخزن")
                st.dataframe(pd.DataFrame([{"المادة":m,"الكمية المرتجعة":f"{q:,.3f}"} for m,q in return_items.items()]), use_container_width=True, hide_index=True)

            if extra_items:
                st.warning(f"🔴 تم صرف {len(extra_items)} مادة إضافية من المخزن")
                st.dataframe(pd.DataFrame([{"المادة":m,"الكمية الإضافية":f"{q:,.3f}"} for m,q in extra_items.items()]), use_container_width=True, hide_index=True)

            # HTML المقارنة
            cmp_html = make_comparison_html(oid, sid, supervisor, planned, actual_qty_done, calc, actual_totals, return_items, extra_items)
            st.download_button("🖨️ تقرير المقارنة وأوامر الارتجاع/الصرف (HTML)", cmp_html.encode('utf-8'), f"comparison_shift{sid}.html", "text/html; charset=utf-8", key="dl_cmp")
            st.caption("💡 يحتوي على أمر الارتجاع وأمر الصرف الإضافي — افتح في المتصفح وأطبع")
            st.markdown("---")

            if st.button("🟢 بدء وردية جديدة", type="primary"):
                st.session_state.prod_stage = 'new'
                st.session_state.prod_shift_id = None
                st.session_state.prod_oid = None
                st.session_state.prod_planned = 0
                st.session_state.prod_calc = {}
                st.session_state.prod_tank_actuals = {}
                st.session_state.prod_tank_serials = []
                st.session_state.prod_supervisor = ''
                st.session_state.pop('_return_items', None)
                st.session_state.pop('_extra_items', None)
                st.session_state.pop('_actual_qty_done', None)
                st.rerun()

# ==========================================
# [4] المشتريات والمخزن
# ==========================================
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 المشتريات والمخزن")
    tabs = st.tabs(["🤝 مورد جديد","🚚 فاتورة توريد","💳 دفعات مورد","🔍 كشف حساب مورد","🔧 ضبط المخزن","📊 رصيد المخزن","💰 أسعار المخزون","🗑️ حذف مورد"])

    with tabs[0]:
        with st.form("sf", clear_on_submit=True):
            s1 = st.text_input("اسم المورد الأصلي:*")
            s2 = st.text_input("الاسم التجاري:")
            s3 = st.text_input("رقم السجل:")
            if st.form_submit_button("✅ حفظ"):
                if s1:
                    if run_write("INSERT INTO suppliers(original_name,trade_name,cr_number) VALUES(:o,:t,:c) ON CONFLICT(original_name) DO NOTHING",{"o":s1,"t":s2,"c":s3}):
                        st.success(f"✅ تم تسجيل [{s1}]!")

    with tabs[1]:
        sdf = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if sdf.empty:
            st.warning("أضف موردين أولاً.")
        else:
            if 'pck'      not in st.session_state: st.session_state.pck      = 0
            if 'pitems'   not in st.session_state: st.session_state.pitems   = []
            if 'last_sup' not in st.session_state: st.session_state.last_sup = ""
            pck    = st.session_state.pck
            csup   = st.selectbox("المورد:", sdf['original_name'].tolist(), key=f"psup_{pck}")
            sup_id = int(sdf[sdf['original_name']==csup]['id'].iloc[0])
            # تصفير البنود تلقائياً عند تغيير المورد
            if csup != st.session_state.last_sup:
                st.session_state.pitems   = []
                st.session_state.last_sup = csup
            inv_num = st.text_input("رقم الفاتورة:*", key=f"pin_{pck}")
            pay_tp  = st.selectbox("نوع الدفع:", ["آجل","نقدي","دفع جزئي"], key=f"ppt_{pck}")
            adv_proc = 0.0
            if pay_tp != "نقدي":
                adv_proc = st.number_input("الدفعة المقدمة (ريال):", min_value=0.0, value=0.0, key=f"padv_{pck}")
            else:
                st.info("💵 دفع نقدي — لا توجد دفعة مقدمة")

            # ---- إضافة البنود ----
            st.markdown("**➕ أضف مواد الفاتورة (بند بعد بند):**")
            with st.form(f"aitf_{pck}", clear_on_submit=True):
                ci1,ci2,ci3 = st.columns(3)
                ms = ci1.selectbox("المادة:", raw_materials_list)
                iq = ci2.number_input("الكمية:", min_value=0.0, value=0.0)
                ip = ci3.number_input("سعر الوحدة:", min_value=0.0, value=0.0)
                if st.form_submit_button("➕ إضافة بند"):
                    if iq > 0 and ip > 0:
                        st.session_state.pitems.append({
                            "المادة": ms, "الكمية": iq,
                            "سعر الوحدة": ip, "الإجمالي": round(iq*ip, 2)
                        })
                        st.rerun()
                    else:
                        st.warning("أدخل كمية وسعر صحيحين")

            # ---- عرض البنود الحالية ----
            if st.session_state.pitems:
                idf = pd.DataFrame(st.session_state.pitems)
                st.dataframe(idf, use_container_width=True, hide_index=True)

                sub   = round(idf['الإجمالي'].sum(), 2)
                vat   = round(sub * 0.15, 2)
                grand = round(sub + vat, 2)
                net_af = round(grand - adv_proc, 2)

                _c1,_c2,_c3,_c4 = st.columns(4)
                _c1.metric("قبل الضريبة",              f"{sub:,.2f} ر")
                _c2.metric("ضريبة 15%",                f"{vat:,.2f} ر")
                _c3.metric("إجمالي الفاتورة مع الضريبة", f"{grand:,.2f} ر")
                _c4.metric("المتبقي بعد المقدم",        f"{net_af:,.2f} ر")

                _sup_total = float(run_query("SELECT COALESCE(SUM(total_price*1.15),0) as t FROM procurement WHERE supplier_id=:s",{"s":sup_id})['t'].iloc[0])
                _sup_paid  = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE supplier_id=:s",{"s":sup_id})['t'].iloc[0])
                st.info(f"📊 رصيد المورد الحالي: إجمالي فواتيره {_sup_total:,.2f} ر | مدفوع {_sup_paid:,.2f} ر | **مستحق {_sup_total-_sup_paid:,.2f} ر**")

                st.markdown("---")
                cb1, cb2 = st.columns(2)

                # ---- اعتماد الفاتورة كوحدة واحدة ----
                if cb1.button("✅ اعتماد الفاتورة كاملةً", type="primary"):
                    if not inv_num:
                        st.error("❌ أدخل رقم الفاتورة أولاً!")
                    elif len(st.session_state.pitems) == 0:
                        st.error("❌ أضف بنداً واحداً على الأقل!")
                    else:
                        # ---- تجميع بيانات الفاتورة ----
                        mat_summary = f"[{inv_num}] " + " / ".join(
                            list(dict.fromkeys(i['المادة'][:12] for i in st.session_state.pitems)))
                        n_items  = int(len(st.session_state.pitems))
                        avg_up   = float(round(sub / max(n_items, 1), 2))
                        total_fp = float(round(sub, 2))

                        # ---- إدراج سجل لكل مادة منفردة في procurement ----
                        # هذا يضمن حساب متوسط السعر بشكل صحيح في لوحة التحكم
                        ok_inv = False
                        for item in st.session_state.pitems:
                            item_qty   = float(item['الكمية'])
                            item_up    = float(item['سعر الوحدة'])
                            item_total = float(item['الإجمالي'])
                            if item_qty > 0:
                                run_write(
                                    "INSERT INTO procurement(supplier_id,material_name,quantity,unit_price,total_price) VALUES(:sid,:mat,:qty,:up,:tp)",
                                    {"sid": int(sup_id),
                                     "mat": str(item['المادة']),
                                     "qty": item_qty,
                                     "up":  item_up,
                                     "tp":  item_total})
                                ok_inv = True

                        if ok_inv:
                            # تحديث المخزون + متوسط السعر المرجح لكل مادة
                            for item in st.session_state.pitems:
                                mat_n = str(item['المادة'])
                                new_q = float(item['الكمية'])
                                new_p = float(item['سعر الوحدة'])

                                # جلب الكمية والسعر الحالي من المخزن
                                cur_inv = run_query(
                                    "SELECT quantity FROM inventory WHERE material_name=:m",
                                    {"m": mat_n})
                                cur_price = run_query(
                                    "SELECT unit_price FROM inventory_prices WHERE material_name=:m",
                                    {"m": mat_n})
                                old_q = float(cur_inv['quantity'].iloc[0]) if not cur_inv.empty else 0.0
                                old_p = float(cur_price['unit_price'].iloc[0]) if not cur_price.empty else 0.0

                                # متوسط التكلفة المرجح
                                total_q = old_q + new_q
                                if total_q > 0:
                                    avg_p = round((old_q * old_p + new_q * new_p) / total_q, 2)
                                else:
                                    avg_p = new_p

                                # تحديث المخزون
                                run_write(
                                    """INSERT INTO inventory(material_name,quantity)
                                       VALUES(:m,:q)
                                       ON CONFLICT(material_name)
                                       DO UPDATE SET quantity=inventory.quantity+EXCLUDED.quantity""",
                                    {"m": mat_n, "q": new_q})

                                # تحديث السعر المرجح في inventory_prices
                                try:
                                    run_write(
                                        """INSERT INTO inventory_prices(material_name,unit_price)
                                           VALUES(:m,:p)
                                           ON CONFLICT(material_name)
                                           DO UPDATE SET unit_price=EXCLUDED.unit_price""",
                                        {"m": mat_n, "p": avg_p})
                                except Exception:
                                    pass

                            # تسجيل الدفعة المقدمة إن وُجدت
                            if adv_proc > 0:
                                new_pid_row = run_query(
                                    "SELECT id FROM procurement WHERE supplier_id=:sid ORDER BY id DESC LIMIT 1",
                                    {"sid": int(sup_id)})
                                if not new_pid_row.empty:
                                    run_write(
                                        "INSERT INTO supplier_payments(supplier_id,procurement_id,amount,payment_type) VALUES(:sid,:pid,:a,'مقدم')",
                                        {"sid": int(sup_id),
                                         "pid": int(new_pid_row['id'].iloc[0]),
                                         "a":   float(round(adv_proc, 2))})

                            st.success(f"✅ تم اعتماد الفاتورة **{inv_num}** — {n_items} بنود — إجمالي مع الضريبة: **{grand:,.2f} ريال**")
                            st.session_state.pitems = []
                            st.session_state.pck   += 1
                            st.rerun()
                        else:
                            st.error("❌ فشل حفظ الفاتورة — تحقق من الاتصال بقاعدة البيانات")

                if cb2.button("🗑️ مسح جميع البنود"):
                    st.session_state.pitems = []
                    st.rerun()
            else:
                st.info("📋 لم تُضف بنوداً بعد — أضف مواد الفاتورة أعلاه.")

    with tabs[2]:
        if 'spk' not in st.session_state: st.session_state.spk = 0
        if 'sp_receipt_html' not in st.session_state: st.session_state.sp_receipt_html = None
        if 'sp_receipt_ready' not in st.session_state: st.session_state.sp_receipt_ready = False

        sdf2 = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if not sdf2.empty:
            spk  = st.session_state.spk
            ss   = st.selectbox("المورد:", sdf2['original_name'].tolist(), key=f"sp_sup_{spk}")
            sid2 = int(sdf2[sdf2['original_name']==ss]['id'].iloc[0])

            prc = run_query("""SELECT p.id,p.material_name,p.total_price,p.date,
                COALESCE(SUM(sp2.amount),0) as paid
                FROM procurement p
                LEFT JOIN supplier_payments sp2 ON sp2.procurement_id=p.id
                WHERE p.supplier_id=:sid
                GROUP BY p.id,p.material_name,p.total_price,p.date
                ORDER BY p.date DESC""", {"sid":sid2})

            if prc.empty:
                st.info("لا توجد فواتير لهذا المورد.")
            else:
                prc['مع_الضريبة'] = prc['total_price'] * 1.15
                prc['المستحق']    = prc['مع_الضريبة'] - prc['paid']
                popts = [
                    f"#{r['id']} | {r['material_name'][:20]} | مستحق: {float(r['المستحق']):,.0f} ر | {r['date']}"
                    for _,r in prc.iterrows()
                ]
                sp_sel  = st.selectbox("اختر الفاتورة:", popts, key=f"sp_inv_{spk}")
                sp_idx  = popts.index(sp_sel)
                sel_row = prc.iloc[sp_idx]
                pid     = int(sel_row['id'])
                inv_due = float(sel_row['المستحق'])
                inv_grand = float(sel_row['مع_الضريبة'])
                inv_paid_so_far = float(sel_row['paid'])

                ca,cb,cc = st.columns(3)
                ca.metric("إجمالي الفاتورة (مع الضريبة)", f"{inv_grand:,.2f} ر")
                cb.metric("المدفوع سابقاً", f"{inv_paid_so_far:,.2f} ر")

                if inv_due <= 0.5:
                    cc.metric("المستحق", "مسدد ✅")
                    st.warning("━" * 40)
                    st.error("⛔ لا توجد دفعات مستحقة في هذه الفاتورة")
                    st.info("✅ هذه الفاتورة مسددة بالكامل — الرجاء اختيار فاتورة أخرى من القائمة أعلاه.")
                else:
                    cc.metric("🔴 المستحق الآن", f"{inv_due:,.2f} ر")
                    _max_pay = round(float(inv_due), 2)
                    sa = st.number_input(
                        f"المبلغ المدفوع (ريال) — الحد الأقصى: {_max_pay:,.2f} ر:",
                        min_value=0.01,
                        max_value=_max_pay,
                        value=_max_pay,
                        key=f"sp_amt_{spk}")

                    # تحقق إضافي: لا يمكن الدفع أكثر من المستحق
                    if sa > _max_pay + 0.01:
                        st.error(f"⛔ المبلغ المدخل ({sa:,.2f} ر) يتجاوز المستحق ({_max_pay:,.2f} ر) — لا يمكن الدفع أكثر من المستحق")
                    else:
                        spt = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"], key=f"sp_pt_{spk}")
                        sb  = st.text_input("البنك / رقم الحوالة:", key=f"sp_bank_{spk}")
                        sn2 = st.text_input("ملاحظات:", key=f"sp_notes_{spk}")

                        if st.button("💳 اعتماد الدفعة وإصدار الإيصال", type="primary", key=f"sp_btn_{spk}"):
                            # تحقق نهائي من قاعدة البيانات قبل الحفظ
                            _live_paid = float(run_query(
                                "SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE procurement_id=:pid",
                                {"pid":int(pid)})['t'].iloc[0])
                            _live_due = inv_grand - _live_paid
                            if sa > _live_due + 0.01:
                                st.error(f"⛔ المبلغ ({sa:,.2f} ر) يتجاوز المستحق الفعلي ({_live_due:,.2f} ر) — تم تحديث البيانات، حاول مرة أخرى.")
                                st.rerun()
                            ok = run_write(
                                "INSERT INTO supplier_payments(supplier_id,procurement_id,amount,payment_type,bank_name,notes) VALUES(:sid,:pid,:a,:pt,:b,:n)",
                                {"sid":int(sid2),"pid":int(pid),"a":float(round(sa,2)),"pt":str(spt),"b":str(sb or ""),"n":str(sn2 or "")})
                            if ok:
                                new_paid = inv_paid_so_far + sa
                                new_due  = inv_grand - new_paid
                                today_r  = datetime.date.today().strftime("%Y/%m/%d")
                                rcpt_no  = f"SPR-{pid}-{datetime.date.today().strftime('%Y%m%d')}"
                                _qr_sp_b64 = make_qr_b64(
                                    f"=== إيصال دفعة مورد ===\nرقم الإيصال: {rcpt_no}\nالمورد: {ss}\nرقم الفاتورة: {pid}\nالمبلغ: {sa:.2f} ريال\nتاريخ الدفع: {today_r}",
                                    color=(30,58,138), module_size=6)
                                due_color = "#16a34a" if new_due <= 0.5 else "#dc2626"
                                due_label = f"{max(0,new_due):,.2f} ريال" + (" ✅ مسدد" if new_due<=0.5 else "")
    
                                sp_html = f"""<!DOCTYPE html>
    <html dir="rtl" lang="ar"><head><meta charset="UTF-8">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    *{{box-sizing:border-box;margin:0;padding:0;}}
    body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;padding:28px;max-width:750px;margin:0 auto;}}
    .hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:16px;}}
    .hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;margin-bottom:3px;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
    .hdr-right{{text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:6px;}}
    .badge{{background:#1E3A8A;color:#fff;padding:6px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
    .badge-en{{background:#eff6ff;color:#1E3A8A;padding:3px 12px;border-radius:8px;font-size:11px;font-weight:700;border:1px solid #1E3A8A;direction:ltr;}}
    .qr-img{{width:70px;height:70px;border:2px solid #1E3A8A;border-radius:6px;}}
    .amt-box{{background:linear-gradient(135deg,#1E3A8A,#2563eb);color:#fff;border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin:14px 0;}}
    .amt-box .lbl{{font-size:13px;opacity:.85;}} .amt-box .lbl-en{{font-size:10px;opacity:.6;direction:ltr;}}
    .amt-box .val{{font-size:26px;font-weight:800;}}
    .grid2{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:14px;}}
    .ig{{background:#f8fafc;border-radius:8px;padding:10px;border-right:3px solid #1E3A8A;}}
    .ig .lbl{{font-size:10px;color:#94a3b8;margin-bottom:3px;}} .ig .val{{font-size:12px;font-weight:700;}}
    .bal{{background:#f1f5f9;border-radius:10px;padding:12px 16px;margin-bottom:14px;}}
    .bal h4{{color:#1E3A8A;font-size:12px;margin-bottom:8px;border-bottom:1px solid #e2e8f0;padding-bottom:5px;}}
    .brow{{display:flex;justify-content:space-between;font-size:12px;padding:4px 0;}}
    .brow.total{{font-weight:700;font-size:13px;border-top:1px solid #e2e8f0;margin-top:4px;padding-top:6px;}}
    .sig-area{{display:flex;justify-content:space-around;margin-top:32px;gap:14px;}}
    .sig-box{{text-align:center;flex:1;}}
    .sig-line{{border-top:2px solid #1e293b;margin-bottom:6px;height:34px;}}
    .sig-ar{{font-size:11px;font-weight:700;}} .sig-en{{font-size:10px;color:#64748b;}}
    .footer{{margin-top:18px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
    @media print{{body{{padding:15px;max-width:100%;}}}}
    </style></head><body>
    <div class="hdr">
      <div><div style="font-size:28px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>الرقم الضريبي: {FACTORY_TAX}</p><p style="margin-top:5px;">رقم الإيصال: <b>{rcpt_no}</b> | {today_r}</p></div>
      <div class="hdr-right"><div class="badge">إيصال دفعة مورد</div><div class="badge-en">Supplier Payment Receipt</div><img class="qr-img" src="data:image/png;base64,{_qr_sp_b64}" alt="QR"></div>
    </div>
    <div class="amt-box">
      <div><div class="lbl">المبلغ المدفوع</div><div class="lbl-en">Amount Paid</div></div>
      <div class="val">{sa:,.2f} ريال</div>
    </div>
    <div class="grid2">
      <div class="ig"><div class="lbl">المورد / Supplier</div><div class="val">{ss}</div></div>
      <div class="ig"><div class="lbl">رقم الفاتورة / Invoice</div><div class="val">#{pid}</div></div>
      <div class="ig"><div class="lbl">طريقة الدفع / Method</div><div class="val">{spt}</div></div>
      <div class="ig"><div class="lbl">البنك / Bank</div><div class="val">{sb or "—"}</div></div>
      <div class="ig"><div class="lbl">التاريخ / Date</div><div class="val">{today_r}</div></div>
      <div class="ig"><div class="lbl">ملاحظات / Notes</div><div class="val">{sn2 or "—"}</div></div>
    </div>
    <div class="bal">
      <h4>📊 ملخص حساب الفاتورة</h4>
      <div class="brow"><span>إجمالي الفاتورة (مع الضريبة)</span><span>{inv_grand:,.2f} ر</span></div>
      <div class="brow"><span>المدفوع سابقاً</span><span>{inv_paid_so_far:,.2f} ر</span></div>
      <div class="brow"><span>هذه الدفعة</span><span style="color:#1E3A8A;font-weight:700;">{sa:,.2f} ر</span></div>
      <div class="brow total"><span>الرصيد المتبقي</span><span style="color:{due_color};">{due_label}</span></div>
    </div>
    <div class="sig-area">
      <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع المحاسب</div><div class="sig-en">Accountant</div></div>
      <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع المورد</div><div class="sig-en">Supplier</div></div>
      <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">ختم الشركة</div><div class="sig-en">Stamp</div></div>
    </div>
    <div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_r}</span></div>
    </body></html>"""
                                st.session_state.sp_receipt_html  = sp_html
                                st.session_state.sp_receipt_ready = True
                                st.success(f"✅ دفعة {sa:,.2f} ريال | متبقي: {max(0,new_due):,.2f} ريال")
                                st.session_state.spk += 1

            if st.session_state.sp_receipt_ready and st.session_state.sp_receipt_html:
                st.download_button("🖨️ طباعة الإيصال (HTML)",
                    st.session_state.sp_receipt_html.encode('utf-8'),
                    f"SupReceipt_{st.session_state.spk}.html",
                    "text/html; charset=utf-8", key="dl_sp_rcpt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")
                if st.button("🆕 دفعة جديدة", key="new_sp_pmt"):
                    st.session_state.sp_receipt_ready = False
                    st.session_state.sp_receipt_html  = None
                    st.rerun()


    with tabs[3]:
        sdf3 = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if not sdf3.empty:
            ss3 = st.selectbox("المورد:", sdf3['original_name'].tolist(), key="sstmt")
            sid3 = int(sdf3[sdf3['original_name']==ss3]['id'].iloc[0])
            d1,d2 = st.columns(2)
            ds3 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="sds3")
            de3 = d2.date_input("إلى:", datetime.date.today(), key="sde3")
            if st.button("📊 عرض كشف المورد"):
                # جلب الفواتير مع المدفوع لكل فاتورة
                ph = run_query("""SELECT p.id as inv_id, p.date, p.material_name,
                    ROUND(CAST(p.total_price*1.15 AS numeric),2) as قيمة_الفاتورة,
                    COALESCE(SUM(sp2.amount),0) as المدفوع
                    FROM procurement p
                    LEFT JOIN supplier_payments sp2 ON sp2.procurement_id=p.id
                    WHERE p.supplier_id=:sid AND p.date BETWEEN :s AND :e
                    GROUP BY p.id,p.date,p.material_name,p.total_price
                    ORDER BY p.date""", {"sid":sid3,"s":ds3,"e":de3})
                import re
                # استخراج رقم الفاتورة الحقيقي من material_name
                # الشكل المحفوظ: "[رقم الفاتورة] مادة1 / مادة2"
                def _extract_inv_num(mat_name):
                    m = re.match(r'^\[(.+?)\]', str(mat_name))
                    return m.group(1) if m else str(mat_name)
                if not ph.empty:
                    ph['رقم_الفاتورة'] = ph['material_name'].apply(_extract_inv_num)
                    ph['المواد'] = ph['material_name'].apply(
                        lambda x: re.sub(r'^\[.+?\]\s*', '', str(x)))

                # جلب الدفعات مع رقم الفاتورة المرتبطة
                pyh = run_query("""SELECT sp2.payment_date, sp2.amount, sp2.payment_type,
                    sp2.bank_name, sp2.procurement_id as inv_id
                    FROM supplier_payments sp2
                    WHERE sp2.supplier_id=:sid AND sp2.payment_date BETWEEN :s AND :e
                    ORDER BY sp2.payment_date""", {"sid":sid3,"s":ds3,"e":de3})

                ti  = float(ph['قيمة_الفاتورة'].sum()) if not ph.empty else 0.0
                tp2 = float(pyh['amount'].sum()) if not pyh.empty else 0.0
                bal = ti - tp2
                today_stmt = datetime.date.today().strftime("%Y/%m/%d")

                # عرض في Streamlit
                m1,m2,m3 = st.columns(3)
                m1.metric("إجمالي الفواتير (مع الضريبة)", f"{ti:,.2f} ر")
                m2.metric("إجمالي المدفوع", f"{tp2:,.2f} ر")
                m3.metric("🔴 المستحق للمورد", f"{bal:,.2f} ر")
                if not ph.empty:
                    ph['المستحق'] = ph['قيمة_الفاتورة'] - ph['المدفوع']
                    st.markdown("#### الفواتير")
                    _ph_display = ph[['رقم_الفاتورة','date','المواد','قيمة_الفاتورة','المدفوع','المستحق']].rename(columns={'رقم_الفاتورة':'رقم الفاتورة','date':'التاريخ','المواد':'المواد الخام'})
                    st.dataframe(_ph_display, use_container_width=True, hide_index=True)
                if not pyh.empty:
                    st.markdown("#### الدفعات")
                    st.dataframe(pyh.rename(columns={'payment_date':'التاريخ','amount':'المبلغ','payment_type':'الطريقة','bank_name':'البنك','inv_id':'رقم الفاتورة'}), use_container_width=True, hide_index=True)

                # ---- بناء HTML ----
                # جدول: رقم الفاتورة | قيمة الفاتورة | المدفوع | المستحق
                inv_rows_html = ""
                running_bal = 0.0
                if not ph.empty:
                    for _,r in ph.iterrows():
                        fv  = float(r['قيمة_الفاتورة'])
                        paid= float(r['المدفوع'])
                        due = fv - paid
                        inv_rows_html += f"""<tr>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;color:#1E3A8A;">{_extract_inv_num(r['material_name'])}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{r['date']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{re.sub(r"^\[.+?\]\s*","",str(r['material_name']))}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;">{fv:,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;">{paid:,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{due:,.2f}</td>
                        </tr>"""

                pay_rows_html = ""
                if not pyh.empty:
                    running = ti
                    for _,r in pyh.iterrows():
                        running -= float(r['amount'])
                        pay_rows_html += f"""<tr>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{r['payment_date']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;color:#1E3A8A;">{ph[ph['inv_id']==r['inv_id']]['رقم_الفاتورة'].iloc[0] if not ph[ph['inv_id']==r['inv_id']].empty else f"#{int(r['inv_id'])}"}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#16a34a;font-weight:700;">{float(r['amount']):,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{r['payment_type']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{r.get('bank_name','') or '—'}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{max(0,running):,.2f}</td>
                        </tr>"""
                bal_color = "#dc2626" if bal > 0 else "#16a34a"
                sup_stmt_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:28px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:18px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#1E3A8A;color:#fff;padding:6px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
.sup-card{{background:linear-gradient(135deg,#1E3A8A,#2563eb);color:#fff;border-radius:12px;padding:16px 20px;margin-bottom:18px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;}}
.sup-card h2{{font-size:16px;margin-bottom:4px;}} .sup-card p{{font-size:11px;opacity:.85;}}
.period-box{{background:rgba(255,255,255,.2);border-radius:8px;padding:8px 14px;text-align:center;}}
.period-box span{{display:block;font-size:10px;opacity:.8;}} .period-box strong{{font-size:13px;}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px;}}
.s-card{{background:#f1f5f9;border-radius:8px;padding:12px;text-align:center;border-top:3px solid #1E3A8A;}}
.s-card.danger{{border-top-color:#dc2626;background:#fef2f2;}}
.s-card .lbl{{font-size:10px;color:#94a3b8;}} .s-card .val{{font-size:15px;font-weight:700;}}
.section-title{{font-size:13px;font-weight:700;color:#1E3A8A;border-right:4px solid #FBBF24;padding-right:10px;margin:16px 0 8px 0;}}
table{{width:100%;border-collapse:collapse;margin-bottom:14px;font-size:11px;}}
thead th{{background:#1E3A8A;color:#fff;padding:9px 8px;text-align:center;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
.final-box{{background:#1E3A8A;color:#fff;border-radius:12px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin-top:18px;}}
.final-box .lbl{{font-size:13px;opacity:.85;}} .final-box .amount{{font-size:24px;font-weight:800;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:28px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>الرقم الضريبي: {FACTORY_TAX}</p></div>
  <div style="text-align:left;"><div class="badge">كشف حساب مورد</div><p style="margin-top:8px;color:#64748b;font-size:11px;">الفترة: {ds3} — {de3}</p><p style="color:#64748b;font-size:11px;">تاريخ الإصدار: {today_stmt}</p></div>
</div>
<div class="sup-card">
  <div><h2>🤝 {ss3}</h2><p>المورد</p></div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <div class="period-box"><span>من</span><strong>{ds3}</strong></div>
    <div class="period-box"><span>إلى</span><strong>{de3}</strong></div>
  </div>
</div>
<div class="summary">
  <div class="s-card"><div class="lbl">إجمالي الفواتير (مع الضريبة)</div><div class="val">{ti:,.2f} ر</div></div>
  <div class="s-card"><div class="lbl">إجمالي المدفوع</div><div class="val" style="color:#16a34a;">{tp2:,.2f} ر</div></div>
  <div class="s-card danger"><div class="lbl">🔴 المستحق للمورد</div><div class="val" style="color:{bal_color};">{bal:,.2f} ر</div></div>
</div>
{"<div class='section-title'>📄 الفواتير (رقم الفاتورة | قيمة الفاتورة | المدفوع | المستحق)</div><table><thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>المادة</th><th>قيمة الفاتورة (ر)</th><th>المدفوع (ر)</th><th>المستحق (ر)</th></tr></thead><tbody>" + inv_rows_html + "</tbody></table>" if inv_rows_html else ""}
{"<div class='section-title'>💵 الدفعات (تاريخ الدفعة | مبلغ الدفعة | الرصيد المتبقي)</div><table><thead><tr><th>تاريخ الدفعة</th><th>رقم الفاتورة</th><th>مبلغ الدفعة (ر)</th><th>طريقة الدفع</th><th>البنك</th><th>الرصيد الإجمالي المستحق</th></tr></thead><tbody>" + pay_rows_html + "</tbody></table>" if pay_rows_html else ""}
<div class="final-box">
  <div><div class="lbl">الرصيد المستحق للمورد</div><div style="font-size:10px;opacity:.7;">Net Balance Due to Supplier</div></div>
  <div class="amount">{bal:,.2f} ريال</div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 — {today_stmt}</span></div>
</body></html>"""

                col_s1, col_s2 = st.columns(2)
                col_s1.download_button("⬇️ تنزيل CSV", df_to_csv(ph) if not ph.empty else df_to_csv(pd.DataFrame()), f"sup_{ss3}.csv", "text/csv")
                col_s2.download_button("🖨️ طباعة كشف الحساب (HTML)",
                    sup_stmt_html.encode('utf-8'),
                    f"supplier_statement_{ss3}_{datetime.date.today()}.html",
                    "text/html; charset=utf-8", key="dl_sup_stmt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة")

    with tabs[4]:
        with st.form("adf2", clear_on_submit=True):
            ma = st.selectbox("المادة:", raw_materials_list)
            nq = st.number_input("الرصيد الجديد:", min_value=0.0)
            if st.form_submit_button("✅ تحديث"):
                if run_write(
                    """INSERT INTO inventory(material_name,quantity) VALUES(:m,:q)
                       ON CONFLICT(material_name) DO UPDATE SET quantity=EXCLUDED.quantity""",
                    {"m":ma,"q":float(nq)}):
                    st.success(f"✅ تم تحديث [{ma}]!")

    with tabs[5]:
        idf2 = run_query("SELECT material_name as المادة,quantity as الكمية FROM inventory ORDER BY material_name")
        st.dataframe(idf2 if not idf2.empty else pd.DataFrame(),use_container_width=True)
        if not idf2.empty: st.download_button("⬇️ تنزيل",df_to_csv(idf2),"inventory.csv","text/csv")

    with tabs[6]:
        st.markdown("### 💰 ضبط أسعار المخزون")
        st.info("أدخل متوسط سعر الوحدة لكل مادة — يُستخدم لحساب قيمة المخزون في لوحة التحكم")
        try:
            prices_df = run_query("SELECT material_name, unit_price FROM inventory_prices ORDER BY material_name")
        except Exception:
            prices_df = pd.DataFrame()
        if not prices_df.empty:
            for _, pr in prices_df.iterrows():
                mat = str(pr['material_name'])
                cur = float(pr['unit_price'] or 0)
                pc1,pc2,pc3 = st.columns([3,2,1])
                pc1.write(f"**{mat}**")
                import hashlib as _hl
                _mk = _hl.md5(mat.encode()).hexdigest()[:8]
                new_p = pc2.number_input("ريال/وحدة", min_value=0.0, value=cur,
                                          key=f"price_{_mk}", label_visibility="collapsed")
                if pc3.button("💾", key=f"save_p_{_mk}"):
                    run_write("UPDATE inventory_prices SET unit_price=:p WHERE material_name=:m",
                              {"p": float(new_p), "m": mat})
                    st.success(f"✅ تم حفظ سعر {mat}: {new_p:,.2f} ر")
                    st.rerun()
        # زر حفظ الكل - يحفظ القيم الحالية في حقول الإدخال
        st.markdown("---")
        if st.button("💾 حفظ جميع الأسعار دفعة واحدة", type="primary"):
            import hashlib as _hl2
            saved_count = 0
            for _, pr in prices_df.iterrows():
                mat = str(pr['material_name'])
                _mk2 = _hl2.md5(mat.encode()).hexdigest()[:8]
                new_p_all = st.session_state.get(f"price_{_mk2}", float(pr['unit_price'] or 0))
                run_write("UPDATE inventory_prices SET unit_price=:p WHERE material_name=:m",
                          {"p": float(new_p_all), "m": mat})
                saved_count += 1
            st.success(f"✅ تم حفظ {saved_count} سعر في قاعدة البيانات!")
            st.rerun()

    with tabs[7]:
        st.markdown("### 🗑️ حذف مورد")
        st.warning("⚠️ تنبيه: حذف المورد سيحذف جميع بياناته وفواتيره ودفعاته بشكل نهائي!")
        del_sdf = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if del_sdf.empty:
            st.info("لا يوجد موردون.")
        else:
            del_sup = st.selectbox("اختر المورد للحذف:", del_sdf['original_name'].tolist(), key="del_sup")
            del_sid = int(del_sdf[del_sdf['original_name']==del_sup]['id'].iloc[0])
            # إحصائيات المورد
            _del_inv_count = run_query("SELECT COUNT(*) as c FROM procurement WHERE supplier_id=:s",{"s":del_sid})
            _del_pay_count = run_query("SELECT COUNT(*) as c FROM supplier_payments WHERE supplier_id=:s",{"s":del_sid})
            st.info(f"📋 هذا المورد لديه: **{int(_del_inv_count['c'].iloc[0])} فاتورة** و **{int(_del_pay_count['c'].iloc[0])} دفعة** مسجلة")
            if 'confirm_del_sup' not in st.session_state: st.session_state.confirm_del_sup = False
            if st.button("🗑️ حذف هذا المورد نهائياً", type="primary"):
                st.session_state.confirm_del_sup = True
            if st.session_state.confirm_del_sup:
                st.error(f"هل أنت متأكد من حذف المورد **{del_sup}** وكل بياناته؟")
                col_yes, col_no = st.columns(2)
                if col_yes.button("✅ نعم، احذف نهائياً", key="yes_del"):
                    run_write("DELETE FROM supplier_payments WHERE supplier_id=:s",{"s":del_sid})
                    run_write("DELETE FROM procurement WHERE supplier_id=:s",{"s":del_sid})
                    run_write("DELETE FROM suppliers WHERE id=:s",{"s":del_sid})
                    st.success(f"✅ تم حذف المورد [{del_sup}] وجميع بياناته!")
                    st.session_state.confirm_del_sup = False
                    st.rerun()
                if col_no.button("❌ إلغاء", key="no_del"):
                    st.session_state.confirm_del_sup = False
                    st.rerun()

# ==========================================
# [5] الشحن والفواتير
# ==========================================
elif menu == "💰 الشحن والفواتير":
    st.subheader("💰 الشحن والفواتير")
    tabs = st.tabs(["🚚 أمر تسليم","📄 فاتورة ضريبية","🏦 سند قبض","🔍 استعلام فواتير","🏷️ بطاقات QR"])

    # ---- دوال HTML للشحن ----
    def _sv(v):
        """قيمة آمنة — تُرجع النص أو شرطة لو فارغة/None"""
        if v is None: return "—"
        s = str(v).strip()
        return s if s and s not in ("None","nan","NaN","") else "—"

    def make_delivery_html(did, oid, customer_name, tank_use, tank_capacity, tank_type,
                           qty, serials_list, driver_name, car_plate, driver_iqama, today_str):
        tc  = _sv(tank_capacity)
        tu  = _sv(tank_use)
        tt  = _sv(tank_type)
        tank_desc = f"خزان {tu} — سعة {tc} — {tt}"
        tank_desc_en = f"Tank {tu} | Capacity: {tc} | Install: {tt}"
        sn_rows = "".join(
            f'''<tr>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:600;">{i+1}</td>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;font-family:monospace;font-size:11px;">{sn}</td>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{tank_desc}</td>
            </tr>'''
            for i,sn in enumerate(serials_list))
        # QR data for delivery
        qr_do_data = (
            f"=== أمر تسليم ===\n"
            f"رقم التسليم: {did}\n"
            f"رقم الطلبية: {oid}\n"
            f"العميل: {customer_name}\n"
            f"عدد الخزانات: {qty}\n"
            f"النوع: {tu} — سعة {tc}\n"
            f"تاريخ التسليم: {today_str}\n"
            f"السائق: {driver_name}\n"
            f"لوحة السيارة: {car_plate}"
        )
        _qr_do_b64 = make_qr_b64(qr_do_data, color=(30,58,138), module_size=7)
        _tpl_do = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;max-width:900px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #1E3A8A;padding-bottom:14px;margin-bottom:20px;}}
.hdr-left h1{{color:#1E3A8A;font-size:20px;font-weight:800;margin-bottom:4px;}}
.hdr-left p{{color:#64748b;font-size:11px;margin:2px 0;}}
.hdr-right{{text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:8px;}}
.badge{{background:#1E3A8A;color:#fff;padding:8px 20px;border-radius:20px;font-size:15px;font-weight:800;}}
.badge-en{{background:#f1f5f9;color:#1E3A8A;padding:4px 14px;border-radius:10px;font-size:12px;font-weight:700;border:1px solid #1E3A8A;direction:ltr;}}
.qr-hdr{{width:80px;height:80px;border:2px solid #1E3A8A;border-radius:8px;overflow:hidden;}}
.qr-hdr canvas,.qr-hdr img{{width:80px!important;height:80px!important;}}
.info-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;background:#f1f5f9;border-radius:10px;padding:16px;margin-bottom:20px;}}
.info-item .lbl{{font-size:10px;color:#94a3b8;display:block;margin-bottom:3px;}}
.info-item .val{{font-size:13px;font-weight:700;color:#1e293b;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px;text-align:center;font-size:12px;}}
tbody td{{padding:8px 10px;border:1px solid #e2e8f0;font-size:12px;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
.sig-section{{margin-top:40px;}}
.sig-title{{font-size:13px;font-weight:700;color:#1E3A8A;border-right:4px solid #FBBF24;padding-right:10px;margin-bottom:24px;}}
.sig-title span{{font-size:11px;color:#64748b;margin-right:8px;direction:ltr;}}
.sig-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:30px;}}
.sig-box{{text-align:center;}}
.sig-line{{border-top:2px solid #1e293b;margin-bottom:8px;height:40px;}}
.sig-ar{{font-size:12px;font-weight:700;color:#1e293b;margin-bottom:2px;}}
.sig-en{{font-size:11px;color:#64748b;}}
.footer{{margin-top:30px;border-top:1px solid #e2e8f0;padding-top:12px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;max-width:100%;}}}}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-left">
    <div style="font-size:32px;margin-bottom:6px;">🏭</div>
    <h1>{FACTORY_NAME}</h1>
    <p>{FACTORY_ADDRESS}</p>
    <p>س.ت: {FACTORY_CR} &nbsp;|&nbsp; الرقم الضريبي: {FACTORY_TAX}</p>
  </div>
  <div class="hdr-right">
    <div class="badge">أمر التسليم رقم: {did}</div>
    <div class="badge-en">Delivery Note No. {did}</div>
    <img src="data:image/png;base64,{_qr_do_b64}" style="width:80px;height:80px;border:2px solid #1E3A8A;border-radius:8px;" alt="QR">
    <p style="font-size:10px;color:#94a3b8;text-align:left;">التاريخ: {today_str}</p>
  </div>
</div>
<div class="info-grid">
  <div class="info-item"><span class="lbl">العميل / Customer</span><span class="val">{customer_name}</span></div>
  <div class="info-item"><span class="lbl">رقم الطلبية / Order No.</span><span class="val">{oid}</span></div>
  <div class="info-item"><span class="lbl">التاريخ / Date</span><span class="val">{today_str}</span></div>
  <div class="info-item"><span class="lbl">نوع الخزان / Tank Type</span><span class="val">{tu}</span></div>
  <div class="info-item"><span class="lbl">السعة / Capacity</span><span class="val">{tc}</span></div>
  <div class="info-item"><span class="lbl">نوع التركيب / Installation</span><span class="val">{tt}</span></div>
  <div class="info-item"><span class="lbl">عدد الخزانات / Qty</span><span class="val">{qty} خزان</span></div>
  <div class="info-item"><span class="lbl">اسم السائق / Driver</span><span class="val">{driver_name}</span></div>
  <div class="info-item"><span class="lbl">رقم اللوحة / Plate</span><span class="val">{car_plate}</span></div>
  <div class="info-item"><span class="lbl">رقم الإقامة / Iqama</span><span class="val">{driver_iqama}</span></div>
</div>
<table>
  <thead><tr><th>#</th><th>الرقم التسلسلي / Serial Number</th><th>وصف الخزان / Tank Description</th></tr></thead>
  <tbody>{sn_rows}</tbody>
</table>
<div class="sig-section">
  <div class="sig-title">التوقيعات <span>/ Signatures</span></div>
  <div class="sig-grid">
    <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع السائق واسمه</div><div class="sig-en">Driver Signature &amp; Name</div></div>
    <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع موقع الاستلام</div><div class="sig-en">Receiver's Signature</div></div>
    <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">ختم الموقع</div><div class="sig-en">Site Stamp</div></div>
  </div>
</div>
<div class="footer">
  <span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span>
  <span>نظام ERP v7.0 | {today_str}</span>
</div>

</body></html>"""
        return _tpl_do

    def make_invoice_html(inv_n, did, oid, customer_name, cr_number, tax_number,
                          tank_use, tank_capacity, tank_type,
                          qty, unit_price, serials_list,
                          sub, vat, grand, adv_d, net, today_str):
        tc  = _sv(tank_capacity)
        tu  = _sv(tank_use)
        tt  = _sv(tank_type)
        tank_desc    = f"خزان {tu} — سعة {tc} — {tt}"
        tank_desc_en = f"Fibreglass Tank {tu} | Capacity: {tc} | {tt}"
        sn_rows_inv  = "".join(
            f'''<tr>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:600;">{i+1}</td>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;font-family:monospace;font-size:11px;">{sn}</td>
              <td style="padding:7px 10px;border:1px solid #e2e8f0;text-align:center;">{tank_desc}</td>
            </tr>'''
            for i,sn in enumerate(serials_list))
        qr_inv_data = (
            f"=== فاتورة مبيعات ===\n"
            f"رقم الفاتورة: {inv_n}\n"
            f"رقم التسليم: {did}\n"
            f"رقم الطلبية: {oid}\n"
            f"العميل: {customer_name}\n"
            f"عدد الخزانات: {qty}\n"
            f"النوع: {tu} — سعة {tc}\n"
            f"الإجمالي: {grand:.2f} ريال\n"
            f"المبلغ المطلوب: {net:.2f} ريال\n"
            f"تاريخ الفاتورة: {today_str}\n"
            f"الرقم الضريبي: {tax_number}"
        )
        _qr_inv_b64  = make_qr_b64(qr_inv_data, color=(220,38,38), module_size=7)
        _tpl_inv = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;max-width:900px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #1E3A8A;padding-bottom:14px;margin-bottom:20px;}}
.hdr-left h1{{color:#1E3A8A;font-size:20px;font-weight:800;margin-bottom:4px;}}
.hdr-left p{{color:#64748b;font-size:11px;margin:2px 0;}}
.hdr-right{{text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:8px;}}
.badge-inv{{background:#dc2626;color:#fff;padding:8px 20px;border-radius:20px;font-size:15px;font-weight:800;}}
.badge-en{{background:#fff0f0;color:#dc2626;padding:4px 14px;border-radius:10px;font-size:12px;font-weight:700;border:1px solid #dc2626;direction:ltr;}}
.qr-hdr{{width:90px;height:90px;border:2px solid #dc2626;border-radius:8px;overflow:hidden;}}
.qr-hdr canvas,.qr-hdr img{{width:90px!important;height:90px!important;}}
.parties{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:18px;}}
.party-box{{background:#f8fafc;border-radius:10px;padding:14px;border-right:4px solid #1E3A8A;}}
.party-box h3{{color:#1E3A8A;font-size:12px;margin-bottom:8px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;}}
.party-box p{{font-size:11px;margin:3px 0;color:#475569;}}
table{{width:100%;border-collapse:collapse;margin-bottom:14px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px;text-align:center;font-size:12px;}}
tbody td{{padding:8px 10px;border:1px solid #e2e8f0;font-size:12px;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
.sn-table thead th{{background:#374151;}}
.totals{{background:#f1f5f9;border-radius:10px;padding:14px;margin-bottom:16px;}}
.trow{{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #e2e8f0;font-size:13px;}}
.trow:last-child{{border:none;}}
.net-box{{background:#1E3A8A;color:#fff;border-radius:10px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;}}
.net-box .lbl{{font-size:13px;opacity:.85;}}
.net-box .lbl-en{{font-size:10px;opacity:.65;}}
.net-box .amount{{font-size:24px;font-weight:800;}}
.footer{{margin-top:24px;border-top:1px solid #e2e8f0;padding-top:12px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;max-width:100%;}}}}
</style>
</head>
<body>
<div class="hdr">
  <div class="hdr-left">
    <div style="font-size:32px;margin-bottom:6px;">🏭</div>
    <h1>{FACTORY_NAME}</h1>
    <p>{FACTORY_ADDRESS}</p>
    <p>س.ت: {FACTORY_CR} &nbsp;|&nbsp; الرقم الضريبي: {FACTORY_TAX}</p>
    <p style="margin-top:6px;color:#64748b;">رقم الفاتورة: <b>{inv_n}</b> &nbsp;|&nbsp; التاريخ: {today_str}</p>
  </div>
  <div class="hdr-right">
    <div class="badge-inv">فاتورة ضريبية رسمية</div>
    <div class="badge-en">TAX INVOICE</div>
    <img src="data:image/png;base64,{_qr_inv_b64}" style="width:90px;height:90px;border:2px solid #dc2626;border-radius:8px;" alt="QR">
    <p style="font-size:9px;color:#94a3b8;text-align:left;">امسح للتحقق / Scan to Verify</p>
  </div>
</div>
<div class="parties">
  <div class="party-box">
    <h3>🏭 البائع / Seller</h3>
    <p><b>{FACTORY_NAME}</b></p>
    <p>{FACTORY_ADDRESS}</p>
    <p>س.ت: {FACTORY_CR}</p>
    <p>الرقم الضريبي: {FACTORY_TAX}</p>
  </div>
  <div class="party-box">
    <h3>👤 المشتري / Buyer</h3>
    <p><b>{customer_name}</b></p>
    <p>س.ت: {cr_number}</p>
    <p>الرقم الضريبي: {tax_number}</p>
    <p>أمر التسليم: #{did}</p>
  </div>
</div>
<table>
  <thead>
    <tr>
      <th>الوصف / Description</th>
      <th>النوع / Type</th>
      <th>السعة / Capacity</th>
      <th>الكمية / Qty</th>
      <th>سعر الوحدة / Unit Price</th>
      <th>الإجمالي / Total</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align:right;padding-right:12px;">خزانات فايبر جلاس<br><span style="font-size:10px;color:#64748b;">Fibreglass Tanks</span></td>
      <td style="text-align:center;">{tu}</td>
      <td style="text-align:center;">{tc}</td>
      <td style="text-align:center;">{qty}</td>
      <td style="text-align:center;">{unit_price:,.2f} ر</td>
      <td style="text-align:center;font-weight:700;">{sub:,.2f} ر</td>
    </tr>
  </tbody>
</table>
<p style="font-size:12px;font-weight:700;color:#1E3A8A;border-right:4px solid #FBBF24;padding-right:10px;margin-bottom:8px;">الأرقام التسلسلية للخزانات / Tank Serial Numbers</p>
<table class="sn-table">
  <thead><tr><th>#</th><th>الرقم التسلسلي / Serial Number</th><th>وصف الخزان / Description</th></tr></thead>
  <tbody>{sn_rows_inv}</tbody>
</table>
<div class="totals">
  <div class="trow"><span>المبلغ قبل الضريبة / Subtotal</span><span>{sub:,.2f} ر</span></div>
  <div class="trow"><span>ضريبة القيمة المضافة 15% / VAT 15%</span><span>{vat:,.2f} ر</span></div>
  <div class="trow"><span style="font-weight:700;">الإجمالي شامل الضريبة / Total incl. VAT</span><span style="font-weight:700;">{grand:,.2f} ر</span></div>
  <div class="trow"><span>خصم الدفعة المقدمة / Advance Deducted</span><span style="color:#dc2626;">- {adv_d:,.2f} ر</span></div>
</div>
<div class="net-box">
  <div><div class="lbl">الصافي المستحق</div><div class="lbl-en">Net Amount Due</div></div>
  <div class="amount">{net:,.2f} ريال</div>
</div>
<div class="footer">
  <span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span>
  <span>نظام ERP v7.0 | {today_str}</span>
</div>

</body></html>"""
        return _tpl_inv

    def make_qr_labels_html(serials_list, tank_use, tank_capacity, tank_type,
                             order_id, customer_name, today_str):
        """
        بتولد HTML للبطاقات — الـ QR يتولد offline بـ Python مباشرة
        نفس طريقة الفاتورة وأمر التسليم: base64 inline في HTML بدون API ولا CDN
        """
        tc  = _sv(tank_capacity)
        tu  = _sv(tank_use)
        tt  = _sv(tank_type)

        # توليد QR لكل بطاقة — API مباشرة لضمان جودة عالية وقراءة سليمة
        cards_data = []
        for i, sn in enumerate(serials_list):
            qr_text = (
                f"SN:{sn}|ORDER:{order_id}|"
                f"CAPACITY:{tc}|USE:{tu}|TYPE:{tt}|"
                f"DATE:{today_str}|SEQ:{i+1}/{len(serials_list)}"
            )
            qr_b64 = _make_qr_fallback(qr_text, color=(30,58,138), module_size=10)
            cards_data.append({
                "sn": sn,
                "qr_b64": qr_b64,
                "index": i + 1,
                "total": len(serials_list)
            })

        # بناء صفحات HTML — كل بطاقة A4 مستقلة مع QR كـ base64 inline
        label_pages = ""
        for item in cards_data:
            label_pages += f"""
<div class="a4-page">
  <div class="card">
    <div class="card-header">
      <div class="header-left">
        <div class="factory-icon">🏭</div>
        <div>
          <div class="factory-name">{FACTORY_NAME}</div>
          <div class="factory-sub">Fibreglass Tank Manufacturer</div>
          <div class="factory-addr">{FACTORY_ADDRESS}</div>
        </div>
      </div>
      <div class="header-right">
        <div class="card-badge">بطاقة تعريف الخزان</div>
        <div class="card-badge-en">Tank ID Card</div>
      </div>
    </div>
    <div class="sn-bar">{item['sn']}</div>
    <div class="card-body">
      <div class="info-col">
        <div class="info-grid">
          <div class="ig"><div class="ig-lbl">نوع الاستخدام</div><div class="ig-val">{tu}</div></div>
          <div class="ig"><div class="ig-lbl">Type of Use</div><div class="ig-val ltr">{tu}</div></div>
          <div class="ig"><div class="ig-lbl">السعة</div><div class="ig-val">{tc}</div></div>
          <div class="ig"><div class="ig-lbl">Capacity</div><div class="ig-val ltr">{tc}</div></div>
          <div class="ig"><div class="ig-lbl">نوع التركيب</div><div class="ig-val">{tt}</div></div>
          <div class="ig"><div class="ig-lbl">Installation</div><div class="ig-val ltr">{tt}</div></div>
          <div class="ig"><div class="ig-lbl">رقم الطلبية</div><div class="ig-val">{order_id}</div></div>
          <div class="ig"><div class="ig-lbl">Order No.</div><div class="ig-val ltr">{order_id}</div></div>
          <div class="ig"><div class="ig-lbl">العميل</div><div class="ig-val">{customer_name}</div></div>
          <div class="ig"><div class="ig-lbl">Customer</div><div class="ig-val ltr">{customer_name}</div></div>
          <div class="ig"><div class="ig-lbl">تاريخ الإنتاج</div><div class="ig-val">{today_str}</div></div>
          <div class="ig"><div class="ig-lbl">Production Date</div><div class="ig-val ltr">{today_str}</div></div>
        </div>
      </div>
      <div class="qr-col">
        <img src="data:image/png;base64,{item['qr_b64']}" class="qr-img" alt="QR">
        <div class="qr-caption">امسح للتحقق<br>Scan to Verify</div>
        <div class="seq-badge">خزان {item['index']} من {item['total']}<br>Tank {item['index']} of {item['total']}</div>
      </div>
    </div>
    <div class="card-footer">
      <span>{FACTORY_NAME} — {FACTORY_ADDRESS}</span>
      <span>نظام ERP v7.0 | {today_str}</span>
    </div>
  </div>
</div>"""

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;background:#e2e8f0;color:#1e293b;}}
.a4-page{{
  width:210mm;min-height:297mm;
  background:#fff;margin:0 auto 20px auto;
  padding:14mm 14mm;
  page-break-after:always;
  display:flex;flex-direction:column;justify-content:center;
}}
.card{{
  width:100%;border:3px solid #1E3A8A;border-radius:14px;
  overflow:hidden;box-shadow:0 4px 20px rgba(30,58,138,.12);
}}
/* هيدر */
.card-header{{
  background:linear-gradient(135deg,#1E3A8A 0%,#2563eb 100%);
  color:#fff;padding:14px 18px;
  display:flex;justify-content:space-between;align-items:center;
}}
.header-left{{display:flex;gap:10px;align-items:center;}}
.factory-icon{{font-size:30px;}}
.factory-name{{font-size:16px;font-weight:800;margin-bottom:2px;}}
.factory-sub{{font-size:10px;opacity:.8;direction:ltr;}}
.factory-addr{{font-size:9px;opacity:.7;margin-top:1px;}}
.header-right{{text-align:center;}}
.card-badge{{background:rgba(255,255,255,.2);padding:5px 14px;border-radius:20px;font-size:13px;font-weight:700;margin-bottom:3px;}}
.card-badge-en{{font-size:10px;opacity:.8;direction:ltr;}}
/* الرقم المسلسل */
.sn-bar{{
  background:#eff6ff;border-bottom:2px solid #bfdbfe;
  padding:10px 18px;text-align:center;
  font-family:monospace;font-size:17px;font-weight:800;
  color:#1E3A8A;letter-spacing:1px;
}}
/* Body: QR يسار + grid يمين */
.card-body{{
  display:flex;flex-direction:row;gap:0;
  min-height:200px;
}}
.qr-col{{
  background:#f8fafc;border-left:1px solid #e2e8f0;
  padding:18px 16px;
  display:flex;flex-direction:column;align-items:center;
  justify-content:center;gap:8px;
  width:190px;flex-shrink:0;
}}
.qr-img{{
  width:150px;height:150px;
  border:3px solid #1E3A8A;border-radius:8px;
  display:block;
}}
.qr-caption{{font-size:10px;color:#64748b;text-align:center;line-height:1.5;}}
.seq-badge{{
  background:#1E3A8A;color:#fff;
  padding:5px 10px;border-radius:6px;
  font-size:10px;font-weight:700;text-align:center;line-height:1.5;
}}
/* Grid البيانات */
.info-col{{
  flex:1;padding:14px 16px;
  display:flex;flex-direction:column;justify-content:center;
}}
.info-grid{{
  display:grid;grid-template-columns:1fr 1fr;gap:7px;
}}
.ig{{
  background:#f8fafc;border-radius:6px;padding:7px 9px;
  border-right:3px solid #1E3A8A;
}}
.ig-lbl{{font-size:9px;color:#94a3b8;margin-bottom:2px;}}
.ig-val{{font-size:12px;font-weight:700;color:#1e293b;word-break:break-word;}}
.ig-val.ltr{{direction:ltr;text-align:left;font-size:11px;}}
/* فوتر */
.card-footer{{
  background:#f1f5f9;border-top:1px solid #e2e8f0;
  padding:8px 18px;display:flex;
  justify-content:space-between;font-size:9px;color:#64748b;
}}
@media print{{
  body{{background:#fff;}}
  .a4-page{{
    width:210mm;min-height:297mm;
    margin:0;padding:12mm;
    page-break-after:always;
  }}
  .card{{box-shadow:none;}}
}}
</style>
</head>
<body>
{label_pages}
</body></html>"""

    # ===== تبويب 1: أمر تسليم =====
    with tabs[0]:
        odf3 = run_query("""SELECT o.order_id,c.trade_name,o.qty,o.tank_use,o.tank_capacity,o.tank_type,
            o.unit_price,o.advance_paid,c.cr_number,c.tax_number
            FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'""")
        if odf3.empty:
            st.info("لا توجد طلبيات.")
        else:
            if 'dok' not in st.session_state: st.session_state.dok = 0
            pck_d = st.session_state.dok

            sel_d = st.selectbox("الطلبية:", [
                f"{r['order_id']} | {r['trade_name']} | سعة: {str(r['tank_capacity'] or '—').strip() or '—'} | {r['tank_use']}"
                for _,r in odf3.iterrows()], key=f"dsel_{pck_d}")
            oid_d = sel_d.split(" | ")[0]
            or_d  = odf3[odf3['order_id']==oid_d].iloc[0]

            # حساب الكمية المتاحة للشحن
            tanks_made = int(run_query("SELECT COALESCE(SUM(actual_qty),0) as t FROM production_days WHERE order_id=:oid AND status='مغلق'",{"oid":oid_d})['t'].iloc[0])
            tanks_shipped_so_far = int(run_query("SELECT COALESCE(SUM(shipped_qty),0) as t FROM delivery_orders WHERE order_id=:oid",{"oid":oid_d})['t'].iloc[0])
            available_to_ship = tanks_made - tanks_shipped_so_far

            st.info(f"✅ مصنّع: **{tanks_made}** | 🚚 مشحون سابقاً: **{tanks_shipped_so_far}** | 🟢 متاح للشحن الآن: **{available_to_ship}** خزان")
            if available_to_ship <= 0:
                st.error("⛔ لا يوجد كمية مصنعة كافية للشحن.")
            else:
                c1,c2 = st.columns(2)
                shipped = c1.number_input("الكمية المشحونة:", min_value=1, max_value=available_to_ship, value=min(1,available_to_ship), key=f"ship_{pck_d}")
                dn = c2.text_input("اسم السائق:", key=f"dn_{pck_d}")
                c3,c4 = st.columns(2)
                dp = c3.text_input("رقم اللوحة:", key=f"dp_{pck_d}")
                di = c4.text_input("رقم الإقامة:", key=f"di_{pck_d}")

                today_str_d = datetime.date.today().strftime("%Y/%m/%d")

                if st.button("🚀 إصدار أمر التسليم", type="primary", key=f"issue_do_{pck_d}"):
                    # تحقق من الكمية مرة أخرى
                    if shipped > available_to_ship:
                        st.error(f"⛔ لا يوجد كمية مصنعة كافية للشحن. الكمية الجاهزة للشحن الآن هي {available_to_ship} خزان.")
                    else:
                        ok_do = run_write("INSERT INTO delivery_orders(order_id,shipped_qty,driver_name,car_plate,driver_iqama) VALUES(:oid,:sq,:dn,:dp,:di)",
                                          {"oid":oid_d,"sq":int(shipped),"dn":dn,"dp":dp,"di":di})
                        if ok_do:
                            nd = run_query("SELECT delivery_id FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_id DESC LIMIT 1",{"oid":oid_d})
                            did_new = int(nd['delivery_id'].iloc[0]) if not nd.empty else 1

                            # جلب الأرقام التسلسلية — بدون delivery_id (العمود غير موجود في DB)
                            # نحسب كم خزان تم تسليمه قبل هذا الأمر لنأخذ الخزانات التالية
                            prev_shipped = tanks_shipped_so_far  # قبل هذا الأمر
                            all_sn = run_query("""SELECT serial_number FROM production_tanks
                                WHERE order_id=:oid
                                ORDER BY serial_number
                                LIMIT :lim OFFSET :off""",
                                {"oid":oid_d,"lim":int(shipped),"off":prev_shipped})
                            serials_shipped = all_sn['serial_number'].tolist() if not all_sn.empty else [f"SUBUL-SN-{did_new}-{i}" for i in range(1,shipped+1)]

                            # إنشاء الفاتورة تلقائياً
                            sub_auto   = float(shipped) * float(or_d['unit_price'])
                            adv_auto   = (float(or_d['advance_paid'])/float(or_d['qty']))*float(shipped) if float(or_d['qty'])>0 else 0
                            vat_auto   = sub_auto * 0.15
                            grand_auto = sub_auto + vat_auto
                            net_auto   = grand_auto - adv_auto
                            inv_n_auto = generate_invoice_number(did_new)
                            # تحقق من عدم التكرار قبل الإدراج
                            inv_exists = run_query("SELECT invoice_id FROM sales_invoices WHERE delivery_id=:did",{"did":did_new})
                            if inv_exists.empty:
                                run_write("INSERT INTO sales_invoices(delivery_id,order_id,subtotal,vat,grand_total,advance_deducted,net_required) VALUES(:did,:oid,:st,:v,:gt,:ad,:nr)",
                                          {"did":did_new,"oid":oid_d,"st":sub_auto,"v":vat_auto,"gt":grand_auto,"ad":adv_auto,"nr":net_auto})

                            # توليد HTML وحفظه في session_state حتى لا يختفي
                            do_html  = make_delivery_html(did_new, oid_d, or_d['trade_name'],
                                str(or_d['tank_use']), str(or_d['tank_capacity'] or '—'), str(or_d['tank_type']),
                                shipped, serials_shipped, dn, dp, di, today_str_d)
                            inv_html = make_invoice_html(inv_n_auto, did_new, oid_d, or_d['trade_name'],
                                str(or_d['cr_number'] or '—'), str(or_d['tax_number'] or '—'),
                                str(or_d['tank_use']), str(or_d['tank_capacity'] or '—'), str(or_d['tank_type']),
                                shipped, float(or_d['unit_price']), serials_shipped,
                                sub_auto, vat_auto, grand_auto, adv_auto, net_auto, today_str_d)
                            # بطاقة A4 لكل خزان — نفس أسلوب الفواتير
                            qr_html = make_qr_labels_html(
                                serials_list=serials_shipped,
                                tank_use=str(or_d['tank_use']),
                                tank_capacity=str(or_d['tank_capacity'] or '—'),
                                tank_type=str(or_d['tank_type']),
                                order_id=str(oid_d),
                                customer_name=str(or_d['trade_name']),
                                today_str=today_str_d)

                            # حفظ في session_state لعدم الاختفاء
                            st.session_state['last_do_html']     = do_html
                            st.session_state['last_inv_html']    = inv_html
                            st.session_state['last_qr_html']     = qr_html
                            st.session_state['last_did']         = did_new
                            st.session_state['last_inv_n']       = inv_n_auto
                            st.session_state['last_do_ready']    = True

                # عرض أزرار التنزيل دائماً طالما في session_state — لا تختفي
                if st.session_state.get('last_do_ready'):
                    did_show  = st.session_state['last_did']
                    inv_show  = st.session_state['last_inv_n']
                    st.success(f"✅ تم إصدار أمر التسليم #{did_show} والفاتورة {inv_show} — نزّل الملفات قبل المتابعة")
                    col1,col2,col3 = st.columns(3)
                    col1.download_button("🖨️ أمر التسليم (HTML)",
                        st.session_state['last_do_html'].encode('utf-8'),
                        f"DO_{did_show}.html", "text/html; charset=utf-8", key="dl_do_persist")
                    col2.download_button("🧾 الفاتورة (HTML)",
                        st.session_state['last_inv_html'].encode('utf-8'),
                        f"INV_{inv_show}.html", "text/html; charset=utf-8", key="dl_inv_persist")
                    col3.download_button("🏷️ بطاقات QR (HTML)",
                        st.session_state['last_qr_html'].encode('utf-8'),
                        f"QR_{did_show}.html", "text/html; charset=utf-8", key="dl_qr_persist")
                    st.caption("💡 افتح كل ملف في Chrome أو Safari ثم Ctrl+P للطباعة أو حفظ PDF")
                    if st.button("🆕 أمر تسليم جديد", key="clear_do"):
                        st.session_state['last_do_ready'] = False
                        st.session_state.dok += 1
                        st.rerun()

    # ===== تبويب 2: فاتورة ضريبية =====
    with tabs[1]:
        dldf = run_query("""SELECT d.delivery_id,d.order_id,d.shipped_qty,d.delivery_date,
            o.unit_price,o.advance_paid,o.qty as tq,o.tank_use,o.tank_capacity,o.tank_type,
            c.trade_name,c.cr_number,c.tax_number
            FROM delivery_orders d JOIN orders o ON d.order_id=o.order_id JOIN customers c ON o.customer_id=c.id
            ORDER BY d.delivery_id DESC""")
        if dldf.empty:
            st.info("لا توجد أوامر تسليم.")
        else:
            # كل أمر تسليم له مفتاح فريد بناءً على delivery_id
            # نعرض أولاً قائمة الاختيار
            dl_opts = [
                f"أمر #{r['delivery_id']} | {r['order_id']} | {r['trade_name']} | {r['shipped_qty']} خزان | {str(r['tank_capacity'] or '—').strip() or '—'}"
                for _,r in dldf.iterrows()]
            sel_dl = st.selectbox("اختر أمر التسليم لعرض فاتورته:", dl_opts, key="inv_tab_sel")
            did2 = int(sel_dl.split("#")[1].split(" ")[0])
            dr   = dldf[dldf['delivery_id']==did2].iloc[0]

            sub   = float(dr['shipped_qty']) * float(dr['unit_price'])
            adv_d = (float(dr['advance_paid'])/float(dr['tq']))*float(dr['shipped_qty']) if float(dr['tq'])>0 else 0
            vat   = sub * 0.15
            grand = sub + vat
            net   = grand - adv_d
            today_str_inv = datetime.date.today().strftime("%Y/%m/%d")

            st.markdown(f"### 🧾 فاتورة أمر التسليم #{did2}")
            st.markdown(f"**العميل:** {dr['trade_name']} | **الطلبية:** {dr['order_id']} | **نوع الخزان:** {_sv(dr['tank_use'])} سعة {_sv(dr['tank_capacity'])} — {_sv(dr['tank_type'])} | **الكمية:** {int(dr['shipped_qty'])} خزان")

            # جلب الفاتورة المحفوظة لهذا الأمر تحديداً
            saved_inv = run_query(
                "SELECT invoice_id,invoice_date FROM sales_invoices WHERE delivery_id=:did",
                {"did":did2})
            if not saved_inv.empty:
                iid_saved = int(saved_inv['invoice_id'].iloc[0])
                inv_n = f"INV-{datetime.date.today().year}-{iid_saved:06d}"
                st.success(f"✅ الفاتورة محفوظة — رقم: {inv_n}")
            else:
                inv_n = generate_invoice_number(did2)
                st.info(f"📋 فاتورة جديدة — رقم: {inv_n} — ستُحفظ عند الضغط على حفظ")

            # جلب الأرقام التسلسلية لهذا الأمر تحديداً
            _prev_off_inv = int(run_query(
                "SELECT COALESCE(SUM(d2.shipped_qty),0) as t FROM delivery_orders d2 WHERE d2.order_id=:oid AND d2.delivery_id<:did",
                {"oid":str(dr['order_id']),"did":did2})['t'].iloc[0])
            serials_inv = run_query(
                "SELECT serial_number FROM production_tanks WHERE order_id=:oid ORDER BY serial_number LIMIT :lim OFFSET :off",
                {"oid":str(dr['order_id']),"lim":int(dr['shipped_qty']),"off":max(0,_prev_off_inv)})
            # إصلاح: لو ما في أرقام تسلسلية نولد أرقام بديلة مرتبطة بأمر التسليم
            sn_list_inv = serials_inv['serial_number'].tolist() if not serials_inv.empty else [f"SUBUL-SN-{did2}-{i}" for i in range(1, int(dr['shipped_qty'])+1)]

            c1f,c2f,c3f,c4f = st.columns(4)
            c1f.metric("قبل الضريبة", f"{sub:,.2f} ر")
            c2f.metric("ضريبة 15%", f"{vat:,.2f} ر")
            c3f.metric("إجمالي مع الضريبة", f"{grand:,.2f} ر")
            c4f.metric("الصافي المستحق", f"{net:,.2f} ر")

            # توليد HTML الفاتورة الخاصة بهذا الأمر
            inv_html2 = make_invoice_html(
                inv_n, did2, dr['order_id'], dr['trade_name'],
                str(dr['cr_number'] or '—'), str(dr['tax_number'] or '—'),
                str(dr['tank_use']), str(dr['tank_capacity'] or '—'), str(dr['tank_type']),
                int(dr['shipped_qty']), float(dr['unit_price']), sn_list_inv,
                sub, vat, grand, adv_d, net, today_str_inv)

            # توليد بطاقات QR للخزانات الخاصة بهذا الأمر — نفس أسلوب الفواتير
            qr_html2 = make_qr_labels_html(
                serials_list=sn_list_inv,
                tank_use=str(dr['tank_use']),
                tank_capacity=str(dr['tank_capacity'] or '—'),
                tank_type=str(dr['tank_type']),
                order_id=str(dr['order_id']),
                customer_name=str(dr['trade_name']),
                today_str=today_str_inv) if sn_list_inv else None

            col_b1, col_b2, col_b3 = st.columns(3)
            # مفتاح فريد لكل أمر تسليم — يضمن طباعة الفاتورة الصحيحة
            col_b1.download_button(
                f"🖨️ طباعة فاتورة أمر #{did2} (HTML)",
                inv_html2.encode('utf-8'),
                f"INV_{inv_n}.html",
                "text/html; charset=utf-8",
                key=f"dl_inv_do_{did2}")
            if qr_html2:
                col_b2.download_button(
                    f"🏷️ بطاقات QR الخزانات ({len(sn_list_inv)} بطاقة)",
                    qr_html2.encode('utf-8'),
                    f"QR_DO_{did2}.html",
                    "text/html; charset=utf-8",
                    key=f"dl_qr_inv_{did2}")
            else:
                col_b2.info("لا توجد أرقام تسلسلية")
            if saved_inv.empty:
                if col_b3.button("💾 حفظ الفاتورة", key=f"save_inv_do_{did2}"):
                    run_write(
                        "INSERT INTO sales_invoices(delivery_id,order_id,subtotal,vat,grand_total,advance_deducted,net_required) VALUES(:did,:oid,:st,:v,:gt,:ad,:nr)",
                        {"did":did2,"oid":dr['order_id'],"st":sub,"v":vat,"gt":grand,"ad":adv_d,"nr":net})
                    st.success(f"✅ تم حفظ فاتورة أمر التسليم #{did2}!")
                    st.rerun()
            else:
                col_b3.success("✅ محفوظة في قاعدة البيانات")
            st.caption("💡 افتح الملفات في Chrome أو Safari ثم Ctrl+P للطباعة")

    # ===== تبويب 3: سند قبض =====
    with tabs[2]:
        if 'rk' not in st.session_state: st.session_state.rk = 0
        if 'receipt_html' not in st.session_state: st.session_state.receipt_html = None
        if 'receipt_ready' not in st.session_state: st.session_state.receipt_ready = False

        cdf4 = run_query("SELECT id,trade_name,cr_number,tax_number FROM customers ORDER BY trade_name")
        if not cdf4.empty:
            rk = st.session_state.rk
            sc4 = st.selectbox("العميل:", cdf4['trade_name'].tolist(), key=f"rc_cust_{rk}")
            cid4 = int(cdf4[cdf4['trade_name']==sc4]['id'].iloc[0])
            cust_row4 = cdf4[cdf4['trade_name']==sc4].iloc[0]
            odf4 = run_query("SELECT order_id FROM orders WHERE customer_id=:c ORDER BY order_date DESC",{"c":cid4})
            so4 = st.selectbox("الطلبية:", odf4['order_id'].tolist() if not odf4.empty else ["—"], key=f"rc_ord_{rk}")
            c_r1,c_r2 = st.columns(2)
            pa4 = c_r1.number_input("المبلغ (ريال):", min_value=0.0, value=0.0, key=f"rc_amt_{rk}")
            pt4 = c_r2.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"], key=f"rc_pt_{rk}")
            pb4 = st.text_input("اسم البنك / رقم الحوالة:", key=f"rc_bank_{rk}")

            if st.button("💵 اعتماد وإصدار سند القبض", type="primary", key=f"rc_btn_{rk}"):
                if pa4 <= 0:
                    st.error("أدخل مبلغاً صحيحاً!")
                else:
                    ok_r = run_write(
                        "INSERT INTO customer_payments(customer_id,order_id,amount,payment_type,bank_name) VALUES(:ci,:oi,:a,:pt,:b)",
                        {"ci":cid4,"oi":so4,"a":pa4,"pt":pt4,"b":pb4})
                    if ok_r:
                        # جلب رقم السند
                        pay_id = run_query(
                            "SELECT id FROM customer_payments WHERE customer_id=:c ORDER BY id DESC LIMIT 1",
                            {"c":cid4})
                        receipt_no = int(pay_id['id'].iloc[0]) if not pay_id.empty else rk+1
                        today_r = datetime.date.today().strftime("%Y/%m/%d")

                        # حساب الرصيد المتبقي للطلبية
                        order_info = run_query(
                            "SELECT total_price,advance_paid FROM orders WHERE order_id=:oid",{"oid":so4})
                        contract_val = float(order_info['total_price'].iloc[0])*1.15 if not order_info.empty else 0
                        total_paid_so_far = float(run_query(
                            "SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE order_id=:oid",
                            {"oid":so4})['t'].iloc[0])
                        adv_order = float(order_info['advance_paid'].iloc[0]) if not order_info.empty else 0
                        remaining_after = contract_val - adv_order - total_paid_so_far

                        qr_rcpt = f"=== إيصال دفعة عميل ===\nرقم الإيصال: {receipt_no}\nالعميل: {sc4}\nرقم الطلبية: {so4}\nالمبلغ: {pa4:.2f} ريال\nطريقة الدفع: {pt4}\nتاريخ الدفع: {today_r}"
                        _qr_rcpt_b64 = make_qr_b64(qr_rcpt, color=(22,163,74), module_size=6)

                        receipt_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:30px;max-width:800px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #16a34a;padding-bottom:14px;margin-bottom:20px;}}
.hdr-left h1{{color:#1E3A8A;font-size:20px;font-weight:800;margin-bottom:4px;}}
.hdr-left p{{color:#64748b;font-size:11px;margin:2px 0;}}
.hdr-right{{text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:8px;}}
.rcpt-badge{{background:#16a34a;color:#fff;padding:8px 20px;border-radius:20px;font-size:15px;font-weight:800;}}
.rcpt-badge-en{{background:#f0fdf4;color:#16a34a;padding:4px 14px;border-radius:10px;font-size:12px;font-weight:700;border:1px solid #16a34a;direction:ltr;}}
.qr-hdr{{width:80px;height:80px;border:2px solid #16a34a;border-radius:8px;overflow:hidden;}}
.qr-hdr canvas,.qr-hdr img{{width:80px!important;height:80px!important;}}
.amount-box{{
  background:linear-gradient(135deg,#16a34a,#15803d);
  color:#fff;border-radius:14px;padding:20px 24px;
  display:flex;justify-content:space-between;align-items:center;
  margin:20px 0;
}}
.amount-box .lbl{{font-size:14px;opacity:.85;}}
.amount-box .lbl-en{{font-size:11px;opacity:.65;direction:ltr;}}
.amount-box .amount{{font-size:32px;font-weight:800;}}
.info-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;}}
.ig{{background:#f8fafc;border-radius:8px;padding:12px;border-right:3px solid #16a34a;}}
.ig .lbl{{font-size:10px;color:#94a3b8;margin-bottom:4px;}}
.ig .val{{font-size:13px;font-weight:700;}}
.balance-box{{background:#eff6ff;border-radius:10px;padding:14px;margin-bottom:20px;border:1px solid #bfdbfe;}}
.balance-box h4{{color:#1E3A8A;font-size:13px;margin-bottom:8px;}}
.b-row{{display:flex;justify-content:space-between;font-size:12px;padding:4px 0;border-bottom:1px solid #e2e8f0;}}
.b-row:last-child{{border:none;font-weight:700;font-size:13px;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:40px;gap:20px;}}
.sig-box{{text-align:center;flex:1;}}
.sig-line{{border-top:2px solid #1e293b;margin-bottom:8px;height:40px;}}
.sig-lbl-ar{{font-size:12px;font-weight:700;}}
.sig-lbl-en{{font-size:10px;color:#64748b;}}
.footer{{margin-top:24px;border-top:1px solid #e2e8f0;padding-top:12px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;max-width:100%;}}}}
</style></head><body>
<div class="hdr">
  <div class="hdr-left">
    <div style="font-size:32px;margin-bottom:6px;">🏭</div>
    <h1>{FACTORY_NAME}</h1>
    <p>{FACTORY_ADDRESS}</p>
    <p>س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p>
    <p style="margin-top:6px;">رقم السند: <b>{receipt_no}</b> | التاريخ: {today_r}</p>
  </div>
  <div class="hdr-right">
    <div class="rcpt-badge">سند قبض</div>
    <div class="rcpt-badge-en">Payment Receipt</div>
    <img src="data:image/png;base64,{_qr_rcpt_b64}" style="width:80px;height:80px;border:2px solid #16a34a;border-radius:8px;" alt="QR">
    <p style="font-size:9px;color:#94a3b8;text-align:left;">امسح للتحقق</p>
  </div>
</div>
<div class="amount-box">
  <div><div class="lbl">المبلغ المستلم</div><div class="lbl-en">Amount Received</div></div>
  <div class="amount">{pa4:,.2f} ريال</div>
</div>
<div class="info-grid">
  <div class="ig"><div class="lbl">العميل / Customer</div><div class="val">{sc4}</div></div>
  <div class="ig"><div class="lbl">رقم الطلبية / Order No.</div><div class="val">{so4}</div></div>
  <div class="ig"><div class="lbl">طريقة الدفع / Payment Method</div><div class="val">{pt4}</div></div>
  <div class="ig"><div class="lbl">البنك / رقم الحوالة</div><div class="val">{pb4 or '—'}</div></div>
  <div class="ig"><div class="lbl">التاريخ / Date</div><div class="val">{today_r}</div></div>
  <div class="ig"><div class="lbl">رقم السند / Receipt No.</div><div class="val">{receipt_no}</div></div>
</div>
<div class="balance-box">
  <h4>📊 ملخص حساب الطلبية / Order Balance Summary</h4>
  <div class="b-row"><span>إجمالي قيمة العقد شامل الضريبة</span><span>{contract_val:,.2f} ر</span></div>
  <div class="b-row"><span>الدفعة المقدمة</span><span>{adv_order:,.2f} ر</span></div>
  <div class="b-row"><span>إجمالي الدفعات المستلمة (بما فيها هذه الدفعة)</span><span>{total_paid_so_far:,.2f} ر</span></div>
  <div class="b-row"><span>🔴 الرصيد المتبقي</span><span style="color:#dc2626;">{remaining_after:,.2f} ر</span></div>
</div>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl-ar">توقيع المحاسب</div><div class="sig-lbl-en">Accountant Signature</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl-ar">توقيع العميل</div><div class="sig-lbl-en">Customer Signature</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-lbl-ar">ختم الشركة</div><div class="sig-lbl-en">Company Stamp</div></div>
</div>
<div class="footer">
  <span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span>
  <span>نظام ERP v7.0 | {today_r}</span>
</div>

</body></html>"""
                        st.session_state.receipt_html  = receipt_html
                        st.session_state.receipt_ready = True
                        st.session_state.rk += 1
                        st.success(f"✅ تم تسجيل {pa4:,.2f} ريال — سند القبض جاهز للطباعة!")

            if st.session_state.receipt_ready and st.session_state.receipt_html:
                st.download_button("🖨️ طباعة سند القبض (HTML)",
                    st.session_state.receipt_html.encode('utf-8'),
                    f"Receipt_{st.session_state.rk}.html",
                    "text/html; charset=utf-8", key="dl_receipt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P للطباعة أو حفظ PDF")
                if st.button("🆕 سند قبض جديد", key="new_receipt"):
                    st.session_state.receipt_ready = False
                    st.session_state.receipt_html  = None
                    st.rerun()

    # ===== تبويب 4: استعلام فواتير =====
    with tabs[3]:
        cdf5 = run_query("SELECT id,trade_name FROM customers ORDER BY trade_name")
        if not cdf5.empty:
            sc5 = st.selectbox("العميل:", ["الكل"]+cdf5['trade_name'].tolist(), key="iq")
            d1,d2 = st.columns(2)
            ds5 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="ids")
            de5 = d2.date_input("إلى:", datetime.date.today(), key="ide")
            if st.button("🔍 بحث الفواتير"):
                if sc5=="الكل":
                    ir = run_query("""SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,
                        o.tank_use,o.tank_capacity,o.tank_type,si.subtotal,si.vat,
                        si.grand_total,si.advance_deducted,si.net_required
                        FROM sales_invoices si
                        JOIN orders o ON si.order_id=o.order_id
                        JOIN customers c ON o.customer_id=c.id
                        WHERE si.invoice_date BETWEEN :s AND :e
                        ORDER BY si.invoice_date DESC""",{"s":ds5,"e":de5})
                else:
                    ci5 = int(cdf5[cdf5['trade_name']==sc5]['id'].iloc[0])
                    ir = run_query("""SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,
                        o.tank_use,o.tank_capacity,o.tank_type,si.subtotal,si.vat,
                        si.grand_total,si.advance_deducted,si.net_required
                        FROM sales_invoices si
                        JOIN orders o ON si.order_id=o.order_id
                        JOIN customers c ON o.customer_id=c.id
                        WHERE o.customer_id=:cid AND si.invoice_date BETWEEN :s AND :e
                        ORDER BY si.invoice_date DESC""",{"cid":ci5,"s":ds5,"e":de5})

                if ir.empty:
                    st.info("لا توجد فواتير في هذه الفترة.")
                else:
                    st.dataframe(ir, use_container_width=True, hide_index=True)
                    # ملخص إجمالي
                    tot_grand = float(ir['grand_total'].sum())
                    tot_net   = float(ir['net_required'].sum())
                    m1,m2,m3 = st.columns(3)
                    m1.metric("عدد الفواتير", len(ir))
                    m2.metric("إجمالي الفواتير", f"{tot_grand:,.2f} ر")
                    m3.metric("إجمالي الصافي المستحق", f"{tot_net:,.2f} ر")

                    # بناء HTML للطباعة
                    today_q = datetime.date.today().strftime("%Y/%m/%d")
                    filter_lbl = sc5 if sc5 != "الكل" else "جميع العملاء"
                    rows_html = ""
                    for _,r in ir.iterrows():
                        tc_q = _sv(r.get('tank_capacity',''))
                        tu_q = _sv(r.get('tank_use',''))
                        tt_q = _sv(r.get('tank_type',''))
                        rows_html += f"""<tr>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r['invoice_id']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r['invoice_date']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;">{r['trade_name']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{r['order_id']}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{tu_q} / {tc_q}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{float(r['subtotal']):,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;">{float(r['vat']):,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;font-weight:700;">{float(r['grand_total']):,.2f}</td>
                          <td style="padding:8px 10px;border:1px solid #e2e8f0;text-align:center;color:#dc2626;font-weight:700;">{float(r['net_required']):,.2f}</td>
                        </tr>"""

                    inv_report_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:12px;padding:24px;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:18px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#1E3A8A;color:#fff;padding:6px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px;}}
.s-card{{background:#f1f5f9;border-radius:8px;padding:12px;text-align:center;border-top:3px solid #1E3A8A;}}
.s-card .lbl{{font-size:10px;color:#94a3b8;}} .s-card .val{{font-size:15px;font-weight:700;color:#1e293b;}}
table{{width:100%;border-collapse:collapse;margin-bottom:14px;font-size:11px;}}
thead th{{background:#1E3A8A;color:#fff;padding:9px 8px;text-align:center;}}
tbody tr:nth-child(even){{background:#f8fafc;}}
tfoot td{{background:#1E3A8A;color:#fff;font-weight:700;padding:9px 8px;text-align:center;}}
.footer{{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:12px;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:28px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>الرقم الضريبي: {FACTORY_TAX}</p></div>
  <div style="text-align:left;"><div class="badge">تقرير الفواتير</div><p style="margin-top:8px;color:#64748b;font-size:11px;">الفترة: {ds5} — {de5}</p><p style="color:#64748b;font-size:11px;">العميل: {filter_lbl}</p><p style="color:#64748b;font-size:11px;">تاريخ الإصدار: {today_q}</p></div>
</div>
<div class="summary">
  <div class="s-card"><div class="lbl">عدد الفواتير</div><div class="val">{len(ir)}</div></div>
  <div class="s-card"><div class="lbl">إجمالي الفواتير</div><div class="val">{tot_grand:,.2f} ر</div></div>
  <div class="s-card"><div class="lbl">الصافي المستحق</div><div class="val" style="color:#dc2626;">{tot_net:,.2f} ر</div></div>
</div>
<table>
  <thead><tr>
    <th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th><th>الطلبية</th>
    <th>النوع/السعة</th><th>قبل الضريبة</th><th>ضريبة 15%</th><th>الإجمالي</th><th>الصافي المستحق</th>
  </tr></thead>
  <tbody>{rows_html}</tbody>
  <tfoot><tr>
    <td colspan="5">الإجماليات</td>
    <td>{float(ir['subtotal'].sum()):,.2f}</td>
    <td>{float(ir['vat'].sum()):,.2f}</td>
    <td>{tot_grand:,.2f}</td>
    <td>{tot_net:,.2f}</td>
  </tr></tfoot>
</table>
<div class="footer"><span>🏭 {FACTORY_NAME}</span><span>نظام ERP v7.0 — {today_q}</span></div>
</body></html>"""

                    col_q1, col_q2 = st.columns(2)
                    col_q1.download_button("⬇️ تنزيل CSV", df_to_csv(ir), "invoices.csv", "text/csv")
                    col_q2.download_button("🖨️ طباعة التقرير (HTML)",
                        inv_report_html.encode('utf-8'),
                        f"invoices_report_{datetime.date.today()}.html",
                        "text/html; charset=utf-8", key="dl_inv_report")
                    st.caption("💡 افتح ملف HTML في Chrome أو Safari ثم Ctrl+P للطباعة")

    # ===== تبويب 5: بطاقات QR =====
    with tabs[4]:
        st.markdown("#### 🏷️ استعلام وإعادة طباعة بطاقات QR الخزانات")
        st.info("ابحث عن بطاقات الخزانات بالتاريخ أو العميل أو أمر التسليم ثم أعد طباعتها.")

        # فلاتر البحث
        qr_col1, qr_col2, qr_col3 = st.columns(3)
        qr_ds = qr_col1.date_input("من تاريخ:", datetime.date.today() - datetime.timedelta(days=90), key="qr_ds")
        qr_de = qr_col2.date_input("إلى تاريخ:", datetime.date.today(), key="qr_de")

        # قائمة العملاء للفلترة
        _qr_custs = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
        _qr_cust_opts = ["الكل"] + (_qr_custs['trade_name'].tolist() if not _qr_custs.empty else [])
        qr_cust = qr_col3.selectbox("العميل:", _qr_cust_opts, key="qr_cust")

        if st.button("🔍 بحث عن البطاقات", type="primary", key="qr_search_btn"):
            # جلب أوامر التسليم في الفترة المحددة
            if qr_cust == "الكل":
                _qr_deliveries = run_query("""
                    SELECT d.delivery_id, d.order_id, d.shipped_qty, d.delivery_date,
                           c.trade_name, o.tank_use, o.tank_capacity, o.tank_type
                    FROM delivery_orders d
                    JOIN orders o ON d.order_id = o.order_id
                    JOIN customers c ON o.customer_id = c.id
                    WHERE d.delivery_date BETWEEN :s AND :e
                    ORDER BY d.delivery_date DESC
                """, {"s": qr_ds, "e": qr_de})
            else:
                _qr_cid = int(_qr_custs[_qr_custs['trade_name'] == qr_cust]['id'].iloc[0])
                _qr_deliveries = run_query("""
                    SELECT d.delivery_id, d.order_id, d.shipped_qty, d.delivery_date,
                           c.trade_name, o.tank_use, o.tank_capacity, o.tank_type
                    FROM delivery_orders d
                    JOIN orders o ON d.order_id = o.order_id
                    JOIN customers c ON o.customer_id = c.id
                    WHERE o.customer_id = :cid AND d.delivery_date BETWEEN :s AND :e
                    ORDER BY d.delivery_date DESC
                """, {"cid": _qr_cid, "s": qr_ds, "e": qr_de})

            st.session_state['qr_search_results'] = _qr_deliveries.to_dict('records') if not _qr_deliveries.empty else []
            st.session_state['qr_searched'] = True

        # عرض النتائج
        if st.session_state.get('qr_searched'):
            _qr_rows = st.session_state.get('qr_search_results', [])
            if not _qr_rows:
                st.warning("⚠️ لا توجد أوامر تسليم في هذه الفترة.")
            else:
                st.success(f"✅ تم العثور على {len(_qr_rows)} أمر تسليم")

                # جدول النتائج
                _qr_display = pd.DataFrame([{
                    "أمر التسليم": r['delivery_id'],
                    "الطلبية": r['order_id'],
                    "العميل": r['trade_name'],
                    "الكمية": int(r['shipped_qty']),
                    "النوع": f"{_sv(str(r['tank_use']))} / {_sv(str(r['tank_capacity']))}",
                    "تاريخ التسليم": str(r['delivery_date'])
                } for r in _qr_rows])
                st.dataframe(_qr_display, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.markdown("##### 🖨️ إعادة طباعة البطاقات")

                # اختيار أمر تسليم واحد أو الكل
                _qr_opts = [f"أمر #{r['delivery_id']} | {r['order_id']} | {r['trade_name']} | {r['shipped_qty']} خزان | {str(r['delivery_date'])}" for r in _qr_rows]
                _qr_sel_mode = st.radio("طباعة:", ["أمر تسليم محدد", "جميع النتائج دفعة واحدة"], key="qr_print_mode", horizontal=True)

                if _qr_sel_mode == "أمر تسليم محدد":
                    _qr_chosen = st.selectbox("اختر أمر التسليم:", _qr_opts, key="qr_sel_do")
                    _qr_chosen_id = int(_qr_chosen.split("#")[1].split(" ")[0])
                    _qr_chosen_rows = [r for r in _qr_rows if r['delivery_id'] == _qr_chosen_id]
                else:
                    _qr_chosen_rows = _qr_rows

                if st.button("🏷️ توليد بطاقات QR للطباعة", key="qr_gen_btn"):
                    _all_pages = []
                    _total_cards = 0
                    with st.spinner("جاري توليد البطاقات..."):
                        for _qr_row in _qr_chosen_rows:
                            _did_q  = _qr_row['delivery_id']
                            _oid_q  = str(_qr_row['order_id'])
                            _qty_q  = int(_qr_row['shipped_qty'])
                            _date_q = str(_qr_row['delivery_date'])
                            _cust_q = str(_qr_row['trade_name'])
                            _use_q  = str(_qr_row['tank_use'])
                            _cap_q  = str(_qr_row['tank_capacity'] or '—')
                            _typ_q  = str(_qr_row['tank_type'])

                            # جلب الأرقام التسلسلية
                            _prev_q = int(run_query(
                                "SELECT COALESCE(SUM(d2.shipped_qty),0) as t FROM delivery_orders d2 WHERE d2.order_id=:oid AND d2.delivery_id<:did",
                                {"oid":_oid_q, "did":_did_q})['t'].iloc[0])
                            _sn_q = run_query(
                                "SELECT serial_number FROM production_tanks WHERE order_id=:oid ORDER BY serial_number LIMIT :lim OFFSET :off",
                                {"oid":_oid_q, "lim":_qty_q, "off":max(0,_prev_q)})
                            # إصلاح: لو ما في أرقام تسلسلية نولد بديلة مرتبطة بأمر التسليم
                            _sn_list_q = _sn_q['serial_number'].tolist() if not _sn_q.empty else [f"SUBUL-SN-{_did_q}-{i}" for i in range(1, _qty_q+1)]

                            # نفس أسلوب الفواتير تماماً
                            _batch = make_qr_labels_html(
                                serials_list=_sn_list_q,
                                tank_use=_use_q,
                                tank_capacity=_cap_q,
                                tank_type=_typ_q,
                                order_id=_oid_q,
                                customer_name=_cust_q,
                                today_str=_date_q)
                            _all_pages.append(_batch)
                            _total_cards += len(_sn_list_q)

                    if _all_pages:
                        # دمج كل الـ HTML في ملف واحد — كل صفحة A4 مستقلة
                        import re as _re
                        _combined_body = ""
                        for _h in _all_pages:
                            _m = _re.search(r'<body>(.*?)</body>', _h, _re.DOTALL)
                            if _m: _combined_body += _m.group(1)
                        # نأخذ CSS من أول ملف
                        _css_match = _re.search(r'<style>(.*?)</style>', _all_pages[0], _re.DOTALL)
                        _css = _css_match.group(1) if _css_match else ""
                        _qr_reprint_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>{_css}</style></head><body>{_combined_body}</body></html>"""
                        st.success(f"✅ تم توليد {_total_cards} بطاقة جاهزة للطباعة!")
                        _fname = f"QR_Reprint_{qr_ds}_{qr_de}.html"
                        st.download_button(
                            f"🖨️ تنزيل وطباعة {_total_cards} بطاقة (HTML)",
                            _qr_reprint_html.encode('utf-8'),
                            _fname,
                            "text/html; charset=utf-8",
                            key="dl_qr_reprint")
                        st.caption("💡 افتح الملف في Chrome أو Safari ثم Ctrl+P للطباعة — كل بطاقة A4 مستقلة")

# ==========================================
# [6] العمال والأجور
# ==========================================
elif menu == "👷 العمال والأجور":
    st.subheader("👷 نظام الأجور والرواتب")

    # session state
    for _k,_v in [('ak',0),('slk',0),('wk',0),
                  ('adv_rcpt',None),('adv_ready',False),
                  ('sal_rcpt',None),('sal_ready',False)]:
        if _k not in st.session_state: st.session_state[_k]=_v

    tabs = st.tabs(["👤 إضافة عامل","✏️ تعديل/حذف","💵 سلفة","💸 خصم","📅 حضور وانصراف","💰 الرواتب","📋 سجل العمال"])

    # ===== تبويب 1: إضافة عامل =====
    with tabs[0]:
        st.markdown("#### إضافة عامل جديد")
        with st.form("wf", clear_on_submit=True):
            c1w,c2w = st.columns(2)
            wn  = c1w.text_input("الاسم الكامل:*")
            wi  = c2w.text_input("رقم الإقامة:*")
            c3w,c4w = st.columns(2)
            ws  = c3w.date_input("تاريخ الالتحاق:")
            w_sal = c4w.number_input("الراتب الشهري الأساسي (ريال):*", min_value=0.0, value=0.0)
            w_job = st.text_input("المسمى الوظيفي:")
            if st.form_submit_button("✅ حفظ العامل"):
                if wn and wi and w_sal > 0:
                    ok_w = run_write(
                        "INSERT INTO workers(name,iqama_id,start_date,base_salary,job_title) VALUES(:n,:i,:s,:b,:j) ON CONFLICT(iqama_id) DO NOTHING",
                        {"n":wn,"i":wi,"s":ws,"b":float(w_sal),"j":w_job})
                    if not ok_w:
                        # fallback بدون base_salary لو العمود غير موجود
                        run_write("INSERT INTO workers(name,iqama_id,start_date) VALUES(:n,:i,:s) ON CONFLICT(iqama_id) DO NOTHING",
                                  {"n":wn,"i":wi,"s":ws})
                    st.success(f"✅ تم إضافة [{wn}] براتب {w_sal:,.2f} ريال!")
                else:
                    st.error("أدخل الاسم ورقم الإقامة والراتب!")

        # عرض قائمة العمال الحاليين
        st.markdown("#### قائمة العمال")
        wlist = run_query("SELECT name,iqama_id,start_date,COALESCE(base_salary,0) as الراتب,COALESCE(job_title,'—') as الوظيفة FROM workers ORDER BY name")
        if not wlist.empty:
            st.dataframe(wlist.rename(columns={'name':'الاسم','iqama_id':'رقم الإقامة','start_date':'تاريخ الالتحاق'}),
                         use_container_width=True, hide_index=True)

    # ===== تبويب 3: سلفة =====
    with tabs[2]:
        st.markdown("#### اعتماد سلفة")
        ak = st.session_state.ak
        wdf = run_query("SELECT id,name,iqama_id,COALESCE(base_salary,0) as base_salary FROM workers ORDER BY name")
        if wdf.empty:
            st.info("أضف عمالاً أولاً.")
        else:
            ws2 = st.selectbox("العامل:", [f"{r['name']} ({r['iqama_id']})" for _,r in wdf.iterrows()], key=f"adv_sel_{ak}")
            wid = int(wdf.iloc[[f"{r['name']} ({r['iqama_id']})" for _,r in wdf.iterrows()].index(ws2)]['id'])
            wrow = wdf.iloc[[f"{r['name']} ({r['iqama_id']})" for _,r in wdf.iterrows()].index(ws2)]
            base_sal = float(wrow['base_salary'])

            # حساب المستحق حتى اليوم
            today = datetime.date.today()
            days_in_month = 30
            days_worked = today.day
            earned_today = round(base_sal / days_in_month * days_worked, 2)

            # السلف المدفوعة هذا الشهر
            month_str = today.strftime("%Y-%m")
            adv_this_month = float(run_query(
                "SELECT COALESCE(SUM(amount),0) as t FROM worker_advances WHERE worker_id=:w AND status='قيد الانتظار'",
                {"w":int(wid)})['t'].iloc[0])

            remaining = max(0, earned_today - adv_this_month)

            ca,cb,cc = st.columns(3)
            ca.metric("الراتب الشهري", f"{base_sal:,.2f} ر")
            cb.metric(f"المستحق حتى اليوم ({days_worked}/{days_in_month})", f"{earned_today:,.2f} ر")
            cc.metric("السلف المعلقة", f"{adv_this_month:,.2f} ر")

            if remaining <= 0:
                st.error(f"⛔ لا يوجد راتب مستحق لهذا العامل الآن — السلف ({adv_this_month:,.2f} ر) تساوي أو تتجاوز المستحق ({earned_today:,.2f} ر)")
            else:
                st.success(f"✅ يمكن صرف سلفة بحد أقصى: {remaining:,.2f} ريال")
                adv_amt = st.number_input("مبلغ السلفة:", min_value=0.01, max_value=float(remaining), value=float(min(remaining, base_sal/4)), key=f"adv_amt_{ak}")
                adv_note = st.text_input("ملاحظات:", key=f"adv_note_{ak}")

                if st.button("💵 اعتماد السلفة وإصدار الإيصال", type="primary", key=f"adv_btn_{ak}"):
                    ok_adv = run_write("INSERT INTO worker_advances(worker_id,amount,notes) VALUES(:w,:a,:n)",
                                       {"w":int(wid),"a":float(adv_amt),"n":str(adv_note)})
                    if ok_adv:
                        today_str = today.strftime("%Y/%m/%d")
                        rcpt_no = f"ADV-{wid}-{today.strftime('%Y%m%d')}-{ak+1}"
                        _qr_adv = make_qr_b64(f"ADVANCE:{rcpt_no}|WORKER:{wrow['name']}|AMT:{adv_amt:.2f}|DATE:{today_str}", color=(30,58,138), module_size=6)

                        adv_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:28px;max-width:700px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:16px;}}
.hdr h1{{color:#1E3A8A;font-size:17px;font-weight:800;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#d97706;color:#fff;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;}}
.badge-en{{background:#fef3c7;color:#d97706;padding:3px 10px;border-radius:8px;font-size:10px;font-weight:700;border:1px solid #d97706;direction:ltr;}}
.qr-img{{width:65px;height:65px;border:2px solid #d97706;border-radius:6px;}}
.amt-box{{background:linear-gradient(135deg,#d97706,#b45309);color:#fff;border-radius:10px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;margin:12px 0;}}
.amt-box .lbl{{font-size:12px;opacity:.85;}} .amt-box .val{{font-size:24px;font-weight:800;}}
.grid2{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:12px;}}
.ig{{background:#f8fafc;border-radius:7px;padding:9px;border-right:3px solid #d97706;}}
.ig .lbl{{font-size:9px;color:#94a3b8;margin-bottom:2px;}} .ig .val{{font-size:12px;font-weight:700;}}
.bal{{background:#fef3c7;border-radius:8px;padding:10px 14px;margin-bottom:12px;border:1px solid #fbbf24;}}
.bal p{{font-size:12px;margin:3px 0;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:28px;gap:12px;}}
.sig-box{{text-align:center;flex:1;}} .sig-line{{border-top:2px solid #1e293b;margin-bottom:5px;height:30px;}}
.sig-ar{{font-size:11px;font-weight:700;}} .sig-en{{font-size:9px;color:#64748b;}}
.footer{{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:8px;display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;}}
@media print{{body{{padding:12px;max-width:100%;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:24px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>رقم الإيصال: <b>{rcpt_no}</b> | {today_str}</p></div>
  <div style="text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
    <div class="badge">إيصال سلفة</div><div class="badge-en">Advance Receipt</div>
    <img class="qr-img" src="data:image/png;base64,{_qr_adv}" alt="QR">
  </div>
</div>
<div class="amt-box"><div><div class="lbl">مبلغ السلفة</div><div style="font-size:10px;opacity:.6">Amount Advanced</div></div><div class="val">{adv_amt:,.2f} ريال</div></div>
<div class="grid2">
  <div class="ig"><div class="lbl">اسم العامل</div><div class="val">{wrow['name']}</div></div>
  <div class="ig"><div class="lbl">رقم الإقامة</div><div class="val">{wrow['iqama_id']}</div></div>
  <div class="ig"><div class="lbl">التاريخ</div><div class="val">{today_str}</div></div>
  <div class="ig"><div class="lbl">ملاحظات</div><div class="val">{adv_note or '—'}</div></div>
</div>
<div class="bal">
  <p><b>الراتب الشهري:</b> {base_sal:,.2f} ريال</p>
  <p><b>المستحق حتى اليوم ({days_worked}/{days_in_month}):</b> {earned_today:,.2f} ريال</p>
  <p><b>هذه السلفة:</b> {adv_amt:,.2f} ريال</p>
  <p><b>الرصيد المتبقي بعد السلفة:</b> {max(0,remaining-adv_amt):,.2f} ريال</p>
</div>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع العامل</div><div class="sig-en">Worker Signature</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع المحاسب</div><div class="sig-en">Accountant</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">ختم الشركة</div><div class="sig-en">Stamp</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_str}</span></div>
</body></html>"""
                        st.session_state.adv_rcpt  = adv_html
                        st.session_state.adv_ready = True
                        st.success(f"✅ سلفة {adv_amt:,.2f} ريال للعامل {wrow['name']}")
                        st.session_state.ak += 1

            if st.session_state.adv_ready and st.session_state.adv_rcpt:
                st.download_button("🖨️ طباعة إيصال السلفة (HTML)",
                    st.session_state.adv_rcpt.encode('utf-8'),
                    f"Advance_{st.session_state.ak}.html",
                    "text/html; charset=utf-8", key="dl_adv_rcpt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P")
                if st.button("🆕 سلفة جديدة", key="new_adv"):
                    st.session_state.adv_ready = False
                    st.session_state.adv_rcpt  = None
                    st.rerun()

    # ===== تبويب 6: الرواتب =====
    with tabs[5]:
        st.markdown("#### مسير الرواتب")
        slk = st.session_state.slk
        wdf2 = run_query("SELECT id,name,iqama_id,COALESCE(base_salary,0) as base_salary FROM workers ORDER BY name")
        if wdf2.empty:
            st.info("أضف عمالاً أولاً.")
        else:
            ws3 = st.selectbox("اختر العامل:", wdf2['name'].tolist(), key=f"sal_sel_{slk}")
            wid2 = int(wdf2[wdf2['name']==ws3]['id'].iloc[0])
            wrow3 = wdf2[wdf2['name']==ws3].iloc[0]
            base3 = float(wrow3['base_salary'])

            today3 = datetime.date.today()
            days_in_month3 = 30
            days_worked3   = today3.day
            earned3        = round(base3 / days_in_month3 * days_worked3, 2)

            # السلف المعلقة
            adv_total3 = float(run_query(
                "SELECT COALESCE(SUM(amount),0) as t FROM worker_advances WHERE worker_id=:w AND status='قيد الانتظار'",
                {"w":int(wid2)})['t'].iloc[0])
            net_sal3 = max(0, earned3 - adv_total3)

            # الرواتب المدفوعة مسبقاً هذا الشهر
            month_str3 = today3.strftime("%Y-%m")
            paid_this_month = float(run_query(
                "SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE worker_id=:w AND month_year=:m",
                {"w":int(wid2),"m":month_str3})['t'].iloc[0])

            # عرض الملخص - راتب غير قابل للتعديل
            sal_summary_df = pd.DataFrame([
                {"البيان": "📌 الراتب الشهري الأساسي",          "المبلغ (ريال)": round(base3,2)},
                {"البيان": f"📅 المستحق حتى اليوم ({days_worked3}/{days_in_month3} يوم)", "المبلغ (ريال)": round(earned3,2)},
                {"البيان": "➖ السلف المعلقة",                   "المبلغ (ريال)": round(adv_total3,2)},
                {"البيان": "✅ الصافي المستحق",                   "المبلغ (ريال)": round(net_sal3,2)},
            ])
            if paid_this_month > 0:
                sal_summary_df = pd.concat([sal_summary_df, pd.DataFrame([
                    {"البيان": "⚠️ مدفوع هذا الشهر مسبقاً", "المبلغ (ريال)": round(paid_this_month,2)}
                ])], ignore_index=True)
            st.dataframe(sal_summary_df, use_container_width=True, hide_index=True,
                         column_config={"المبلغ (ريال)": st.column_config.NumberColumn(format="%.2f ر")})

            if net_sal3 <= 0.5:
                st.error("⛔ لا يوجد راتب مستحق لهذا العامل الآن — السلف تعادل أو تتجاوز المستحق.")
            else:
                if st.button("💰 اعتماد الراتب وإصدار الإيصال", type="primary", key=f"sal_btn_{slk}"):
                    ok_sal = run_write(
                        "INSERT INTO worker_salaries(worker_id,month_year,base_salary,advances_deducted,net_paid) VALUES(:w,:my,:b,:a,:n)",
                        {"w":int(wid2),"my":month_str3,"b":float(base3),"a":float(adv_total3),"n":float(net_sal3)})
                    if ok_sal:
                        run_write("UPDATE worker_advances SET status='مخصومة' WHERE worker_id=:w AND status='قيد الانتظار'",{"w":int(wid2)})
                        today_str3 = today3.strftime("%Y/%m/%d")
                        rcpt_no3   = f"SAL-{wid2}-{today3.strftime('%Y%m%d')}"
                        _qr_sal = make_qr_b64(f"SALARY:{rcpt_no3}|WORKER:{ws3}|NET:{net_sal3:.2f}|DATE:{today_str3}", color=(22,163,74), module_size=6)

                        sal_html = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;font-size:13px;padding:28px;max-width:700px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:4px solid #16a34a;padding-bottom:12px;margin-bottom:16px;}}
.hdr h1{{color:#1E3A8A;font-size:17px;font-weight:800;}} .hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#16a34a;color:#fff;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;}}
.badge-en{{background:#f0fdf4;color:#16a34a;padding:3px 10px;border-radius:8px;font-size:10px;font-weight:700;border:1px solid #16a34a;direction:ltr;}}
.qr-img{{width:65px;height:65px;border:2px solid #16a34a;border-radius:6px;}}
.amt-box{{background:linear-gradient(135deg,#16a34a,#15803d);color:#fff;border-radius:10px;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;margin:12px 0;}}
.amt-box .val{{font-size:24px;font-weight:800;}}
.grid2{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin-bottom:12px;}}
.ig{{background:#f8fafc;border-radius:7px;padding:9px;border-right:3px solid #16a34a;}}
.ig .lbl{{font-size:9px;color:#94a3b8;margin-bottom:2px;}} .ig .val{{font-size:12px;font-weight:700;}}
.breakdown{{background:#f0fdf4;border-radius:8px;padding:10px 14px;margin-bottom:12px;border:1px solid #86efac;}}
.breakdown p{{font-size:12px;margin:3px 0;}}
.sig-area{{display:flex;justify-content:space-around;margin-top:28px;gap:12px;}}
.sig-box{{text-align:center;flex:1;}} .sig-line{{border-top:2px solid #1e293b;margin-bottom:5px;height:30px;}}
.sig-ar{{font-size:11px;font-weight:700;}} .sig-en{{font-size:9px;color:#64748b;}}
.footer{{margin-top:16px;border-top:1px solid #e2e8f0;padding-top:8px;display:flex;justify-content:space-between;font-size:9px;color:#94a3b8;}}
@media print{{body{{padding:12px;max-width:100%;}}}}
</style></head><body>
<div class="hdr">
  <div><div style="font-size:24px;">🏭</div><h1>{FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p><p>رقم الإيصال: <b>{rcpt_no3}</b> | {today_str3}</p></div>
  <div style="text-align:left;display:flex;flex-direction:column;align-items:flex-end;gap:5px;">
    <div class="badge">إيصال راتب</div><div class="badge-en">Salary Receipt</div>
    <img class="qr-img" src="data:image/png;base64,{_qr_sal}" alt="QR">
  </div>
</div>
<div class="amt-box"><div><div style="font-size:12px;opacity:.85;">صافي الراتب المستحق</div><div style="font-size:10px;opacity:.6">Net Salary</div></div><div class="val">{net_sal3:,.2f} ريال</div></div>
<div class="grid2">
  <div class="ig"><div class="lbl">اسم العامل</div><div class="val">{ws3}</div></div>
  <div class="ig"><div class="lbl">رقم الإقامة</div><div class="val">{wrow3['iqama_id']}</div></div>
  <div class="ig"><div class="lbl">الشهر</div><div class="val">{month_str3}</div></div>
  <div class="ig"><div class="lbl">تاريخ الصرف</div><div class="val">{today_str3}</div></div>
</div>
<div class="breakdown">
  <p><b>الراتب الأساسي الشهري:</b> {base3:,.2f} ريال</p>
  <p><b>أيام العمل ({days_worked3}/{days_in_month3}):</b> المستحق = {earned3:,.2f} ريال</p>
  <p><b>السلف المخصومة:</b> {adv_total3:,.2f} ريال</p>
  <p style="border-top:1px solid #86efac;padding-top:6px;margin-top:6px;"><b>✅ الصافي المدفوع:</b> {net_sal3:,.2f} ريال</p>
</div>
<div class="sig-area">
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع العامل</div><div class="sig-en">Worker Signature</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">توقيع المحاسب</div><div class="sig-en">Accountant</div></div>
  <div class="sig-box"><div class="sig-line"></div><div class="sig-ar">ختم الشركة</div><div class="sig-en">Stamp</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_str3}</span></div>
</body></html>"""
                        st.session_state.sal_rcpt  = sal_html
                        st.session_state.sal_ready = True
                        st.success(f"✅ راتب {net_sal3:,.2f} ريال للعامل {ws3}")
                        st.session_state.slk += 1

            if st.session_state.sal_ready and st.session_state.sal_rcpt:
                st.download_button("🖨️ طباعة إيصال الراتب (HTML)",
                    st.session_state.sal_rcpt.encode('utf-8'),
                    f"Salary_{st.session_state.slk}.html",
                    "text/html; charset=utf-8", key="dl_sal_rcpt")
                st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P")
                if st.button("🆕 راتب جديد", key="new_sal"):
                    st.session_state.sal_ready = False
                    st.session_state.sal_rcpt  = None
                    st.rerun()

    # ===== تبويب 2: تعديل / حذف عامل =====
    with tabs[1]:
        st.markdown("#### تعديل أو حذف عامل")
        wdf_e = run_query("SELECT id,name,iqama_id,COALESCE(base_salary,0) as base_salary,COALESCE(job_title,'') as job_title,COALESCE(phone,'') as phone FROM workers ORDER BY name")
        if wdf_e.empty:
            st.info("لا يوجد عمال.")
        else:
            sel_e = st.selectbox("اختر العامل:", wdf_e['name'].tolist(), key="edit_sel")
            er = wdf_e[wdf_e['name']==sel_e].iloc[0]
            eid = int(er['id'])
            ec1,ec2 = st.columns(2)
            new_name  = ec1.text_input("الاسم:", value=str(er['name']), key="e_name")
            new_iqama = ec2.text_input("رقم الإقامة:", value=str(er['iqama_id']), key="e_iqama")
            ec3,ec4 = st.columns(2)
            new_sal   = ec3.number_input("الراتب الأساسي:", min_value=0.0, value=float(er['base_salary']), key="e_sal")
            new_job   = ec4.text_input("المسمى الوظيفي:", value=str(er['job_title']), key="e_job")
            new_phone = st.text_input("رقم الجوال:", value=str(er['phone']), key="e_phone")
            col_upd, col_del = st.columns(2)
            if col_upd.button("💾 حفظ التعديلات", type="primary"):
                run_write("UPDATE workers SET name=:n,iqama_id=:i,base_salary=:b,job_title=:j,phone=:p WHERE id=:id",
                          {"n":new_name,"i":new_iqama,"b":float(new_sal),"j":new_job,"p":new_phone,"id":eid})
                st.success(f"✅ تم تعديل بيانات [{new_name}]!")
                st.rerun()
            if 'confirm_del_w' not in st.session_state: st.session_state.confirm_del_w = False
            if col_del.button("🗑️ حذف العامل", type="secondary"):
                st.session_state.confirm_del_w = True
            if st.session_state.confirm_del_w:
                st.error(f"⚠️ هل أنت متأكد من حذف [{sel_e}] وكل بياناته؟")
                cy,cn = st.columns(2)
                if cy.button("✅ نعم احذف", key="del_yes_w"):
                    run_write("DELETE FROM worker_attendance WHERE worker_id=:id",{"id":eid})
                    run_write("DELETE FROM worker_deductions WHERE worker_id=:id",{"id":eid})
                    run_write("DELETE FROM worker_advances WHERE worker_id=:id",{"id":eid})
                    run_write("DELETE FROM worker_salaries WHERE worker_id=:id",{"id":eid})
                    run_write("DELETE FROM workers WHERE id=:id",{"id":eid})
                    st.success(f"✅ تم حذف [{sel_e}]!")
                    st.session_state.confirm_del_w = False
                    st.rerun()
                if cn.button("❌ إلغاء", key="del_no_w"):
                    st.session_state.confirm_del_w = False
                    st.rerun()

    # ===== تبويب 4: خصم =====
    with tabs[3]:
        st.markdown("#### تسجيل خصم على عامل")
        if 'ddk' not in st.session_state: st.session_state.ddk = 0
        ddk = st.session_state.ddk
        wdf_d = run_query("SELECT id,name,COALESCE(base_salary,0) as base_salary FROM workers ORDER BY name")
        if wdf_d.empty:
            st.info("لا يوجد عمال.")
        else:
            sel_d = st.selectbox("العامل:", wdf_d['name'].tolist(), key=f"ded_sel_{ddk}")
            did_d = int(wdf_d[wdf_d['name']==sel_d]['id'].iloc[0])
            base_d = float(wdf_d[wdf_d['name']==sel_d]['base_salary'].iloc[0])
            ded_reason = st.selectbox("سبب الخصم:", ["غياب","تأخير","كسر/تلف","مخالفة","أخرى"], key=f"ded_reason_{ddk}")
            ded_amt = st.number_input("مبلغ الخصم (ريال):", min_value=0.0, value=0.0, key=f"ded_amt_{ddk}")
            ded_note = st.text_input("ملاحظة:", key=f"ded_note_{ddk}")
            if st.button("💸 تسجيل الخصم", type="primary", key=f"ded_btn_{ddk}"):
                run_write("INSERT INTO worker_deductions(worker_id,amount,reason,deduction_date) VALUES(:w,:a,:r,CURRENT_DATE)",
                          {"w":did_d,"a":float(ded_amt),"r":f"{ded_reason} - {ded_note}"})
                st.success(f"✅ تم تسجيل خصم {ded_amt:,.2f} ريال على [{sel_d}]!")
                st.session_state.ddk += 1
                st.rerun()
            # عرض الخصومات
            deds = run_query("SELECT deduction_date,amount,reason FROM worker_deductions WHERE worker_id=:w ORDER BY deduction_date DESC",{"w":did_d})
            if not deds.empty:
                st.markdown("##### الخصومات المسجلة:")
                st.dataframe(deds.rename(columns={'deduction_date':'التاريخ','amount':'المبلغ','reason':'السبب'}),
                             use_container_width=True, hide_index=True)
                st.info(f"إجمالي الخصومات: {float(deds['amount'].sum()):,.2f} ريال")

    # ===== تبويب 5: حضور وانصراف =====
    with tabs[4]:
        st.markdown("#### تسجيل الحضور والانصراف")
        wdf_att = run_query("SELECT id,name FROM workers ORDER BY name")
        if wdf_att.empty:
            st.info("لا يوجد عمال.")
        else:
            att_date = st.date_input("تاريخ الحضور:", datetime.date.today(), key="att_date")
            st.markdown(f"**تسجيل حضور يوم: {att_date}**")

            # عرض حالة كل عامل لهذا اليوم
            for _,wr in wdf_att.iterrows():
                wid_a = int(wr['id'])
                existing = run_query(
                    "SELECT status FROM worker_attendance WHERE worker_id=:w AND att_date=:d",
                    {"w":wid_a,"d":att_date})
                cur_status = existing['status'].iloc[0] if not existing.empty else None
                col_n,col_s,col_btn = st.columns([3,2,1])
                col_n.write(f"👤 {wr['name']}")
                status_opts = ["حاضر","غائب","إجازة","مأمورية"]
                default_idx = status_opts.index(cur_status) if cur_status in status_opts else 0
                new_status = col_s.selectbox("", status_opts,
                                              index=default_idx,
                                              key=f"att_{wid_a}_{att_date}",
                                              label_visibility="collapsed")
                if col_btn.button("✅", key=f"att_save_{wid_a}_{att_date}"):
                    try:
                        run_write("""INSERT INTO worker_attendance(worker_id,att_date,status)
                                   VALUES(:w,:d,:s)
                                   ON CONFLICT(worker_id,att_date)
                                   DO UPDATE SET status=EXCLUDED.status""",
                                  {"w":int(wid_a),"d":str(att_date),"s":str(new_status)})
                    except Exception:
                        run_write("UPDATE worker_attendance SET status=:s WHERE worker_id=:w AND att_date=:d",
                                  {"s":str(new_status),"w":int(wid_a),"d":str(att_date)})
                    st.rerun()

            st.markdown("---")
            # تقرير الحضور للفترة
            st.markdown("#### 📊 تقرير الحضور")
            ra1,ra2 = st.columns(2)
            att_from = ra1.date_input("من:", datetime.date.today().replace(day=1), key="att_from")
            att_to   = ra2.date_input("إلى:", datetime.date.today(), key="att_to")
            att_rep  = run_query("""SELECT w.name,
                COUNT(CASE WHEN a.status='حاضر' THEN 1 END) as حضور,
                COUNT(CASE WHEN a.status='غائب' THEN 1 END) as غياب,
                COUNT(CASE WHEN a.status='إجازة' THEN 1 END) as إجازة,
                COUNT(CASE WHEN a.status='مأمورية' THEN 1 END) as مأمورية,
                COUNT(a.id) as إجمالي_مسجل
                FROM workers w
                LEFT JOIN worker_attendance a ON a.worker_id=w.id
                    AND a.att_date BETWEEN :s AND :e
                GROUP BY w.id,w.name ORDER BY w.name""",
                {"s":att_from,"e":att_to})
            if not att_rep.empty:
                st.dataframe(att_rep, use_container_width=True, hide_index=True)
            else:
                st.info("لا توجد بيانات حضور.")

    # ===== تبويب 6 (الرواتب) = تبويب 3 القديم =====
    # تبويب 7 (سجل العمال) = تبويب 4 القديم

    # ===== تبويب 7: سجل العمال =====
    with tabs[6]:
        st.markdown("#### سجل العمال والمدفوعات")
        wdf4 = run_query("SELECT id,name,iqama_id,COALESCE(base_salary,0) as base_salary FROM workers ORDER BY name")
        if wdf4.empty:
            st.info("لا يوجد عمال.")
        else:
            sw = st.selectbox("اختر العامل:", ["الكل"] + wdf4['name'].tolist(), key="wrk_search")
            if sw == "الكل":
                st.dataframe(wdf4.rename(columns={'name':'الاسم','iqama_id':'رقم الإقامة','base_salary':'الراتب الأساسي'}),
                             use_container_width=True, hide_index=True)
            else:
                wid4 = int(wdf4[wdf4['name']==sw]['id'].iloc[0])
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**السلف:**")
                    adv_hist = run_query("SELECT amount,notes,created_at,status FROM worker_advances WHERE worker_id=:w ORDER BY created_at DESC",{"w":wid4})
                    st.dataframe(adv_hist if not adv_hist.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True, hide_index=True)
                with col_b:
                    st.markdown("**الرواتب المدفوعة:**")
                    sal_hist = run_query("SELECT month_year,base_salary,advances_deducted,net_paid,payout_date FROM worker_salaries WHERE worker_id=:w ORDER BY payout_date DESC",{"w":wid4})
                    st.dataframe(sal_hist if not sal_hist.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True, hide_index=True)

# ==========================================
# [7] النظام المحاسبي
# ==========================================
elif menu == "📈 النظام المحاسبي":
    st.subheader("📈 النظام المحاسبي — التقارير المالية")
    c1,c2 = st.columns(2)
    ds_a = c1.date_input("من:", datetime.date.today()-datetime.timedelta(days=365), key="ads")
    de_a = c2.date_input("إلى:", datetime.date.today(), key="ade")
    today_acc = datetime.date.today().strftime("%Y/%m/%d")

    # ===== جلب كل البيانات مرة واحدة =====
    # الإيرادات
    sales_tot = float(run_query("SELECT COALESCE(SUM(grand_total),0) as t FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
    # تكلفة المواد المستهلكة فعلياً في التصنيع
    try:
        ip_df_a = run_query("SELECT material_name, unit_price FROM inventory_prices")
        ip_map_a = {str(r['material_name']): float(r['unit_price'] or 0) for _,r in ip_df_a.iterrows()} if not ip_df_a.empty else {}
    except Exception: ip_map_a = {}
    prod_a = run_query("""SELECT pd.actual_qty,o.resin_exp,o.mat_exp,o.roving_exp,o.tissue_exp,o.catalyst_exp,o.calcium_exp,o.silica_exp
        FROM production_days pd JOIN orders o ON pd.order_id=o.order_id
        WHERE pd.status='مغلق' AND pd.date BETWEEN :s AND :e""", {"s":ds_a,"e":de_a})
    cogs = 0.0
    if not prod_a.empty:
        resin_p = next((v for k,v in ip_map_a.items() if 'راتنج' in k or 'ريزن' in k), 0.0)
        for _,r in prod_a.iterrows():
            q = float(r['actual_qty'] or 0)
            cogs += q*(float(r['resin_exp'] or 0)*resin_p + float(r['mat_exp'] or 0)*ip_map_a.get("ألياف (Mat 450)",0)
                      +float(r['roving_exp'] or 0)*ip_map_a.get("روفرز (Roving 600)",0)
                      +float(r['tissue_exp'] or 0)*ip_map_a.get("تيسو (Tissue)",0)
                      +float(r['catalyst_exp'] or 0)*ip_map_a.get("مصلد (Catalyst)",0)
                      +float(r['calcium_exp'] or 0)*ip_map_a.get("كربونات الكالسيوم",0)
                      +float(r['silica_exp'] or 0)*ip_map_a.get("سيليكا (Silica)",0))
    cogs = round(cogs, 2)
    gross_p = round(sales_tot - cogs, 2)
    # مصاريف التشغيل
    sal_tot  = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
    exp_tot  = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
    op_exp   = round(sal_tot + exp_tot, 2)
    net_inc  = round(gross_p - op_exp, 2)

    # الأصول
    inv_val = 0.0
    try:
        inv_q = run_query("SELECT material_name, quantity FROM inventory WHERE quantity>0")
        if not inv_q.empty:
            for _,r in inv_q.iterrows():
                inv_val += float(r['quantity']) * ip_map_a.get(str(r['material_name']), 0.0)
    except Exception: pass
    inv_val = round(inv_val, 2)
    # ذمم مدينة (مستحق من العملاء)
    recv = float(run_query("""SELECT COALESCE(SUM(o.total_price*1.15 - COALESCE(o.advance_paid,0) -
        COALESCE((SELECT SUM(cp.amount) FROM customer_payments cp WHERE cp.order_id=o.order_id),0)),0) as t
        FROM orders o WHERE o.status != 'ملغاة'""")['t'].iloc[0])
    recv = max(0, round(recv, 2))
    # نقدية (إجمالي تحصيلات - إجمالي مدفوعات)
    cash_in  = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM customer_payments")['t'].iloc[0])
    cash_out = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments")['t'].iloc[0])
    cash_sal = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries")['t'].iloc[0])
    cash_exp = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses")['t'].iloc[0])
    cash_bal = round(cash_in - cash_out - cash_sal - cash_exp, 2)
    total_assets = round(cash_bal + inv_val + recv, 2)

    # الخصوم
    sup_due = float(run_query("""SELECT COALESCE(SUM(p.total_price*1.15 -
        COALESCE((SELECT SUM(sp.amount) FROM supplier_payments sp WHERE sp.supplier_id=p.supplier_id),0)),0) as t
        FROM procurement p""")['t'].iloc[0])
    sup_due = max(0, round(sup_due, 2))
    total_liab = sup_due
    equity = round(total_assets - total_liab, 2)

    tabs = st.tabs(["📊 قائمة الدخل","💰 التدفق النقدي","⚖️ الميزانية العمومية"])

    # ===== تبويب 1: قائمة الدخل =====
    with tabs[0]:
        st.markdown(f"#### قائمة الدخل | من {ds_a} إلى {de_a}")
        income_rows = [
            ("إيرادات المبيعات (مع الضريبة)",      sales_tot,  "إيراد"),
            ("(–) تكلفة البضاعة المباعة (COGS)",    cogs,       "تكلفة"),
            ("══ مجمل الربح (Gross Profit)",         gross_p,    "نتيجة"),
            ("(–) رواتب العمال",                     sal_tot,    "مصروف"),
            ("(–) المصاريف التشغيلية",               exp_tot,    "مصروف"),
            ("══ إجمالي مصاريف التشغيل",             op_exp,     "إجمالي"),
            ("💵 صافي الربح / الخسارة (Net Income)", net_inc,    "صافي"),
        ]
        inc_df = pd.DataFrame(income_rows, columns=["البيان","المبلغ (ريال)","النوع"])
        st.dataframe(inc_df[["البيان","المبلغ (ريال)"]], use_container_width=True, hide_index=True,
                     column_config={"المبلغ (ريال)": st.column_config.NumberColumn(format="%.2f ر")})
        i1,i2,i3 = st.columns(3)
        i1.metric("إجمالي المبيعات", f"{sales_tot:,.2f} ر")
        i2.metric("تكلفة البضاعة المباعة", f"{cogs:,.2f} ر")
        i3.metric("صافي الربح", f"{net_inc:,.2f} ر", delta="ربح ✅" if net_inc>=0 else "خسارة ❌")
        st.download_button("⬇️ تنزيل CSV", df_to_csv(inc_df), "income_statement.csv", "text/csv")
        # HTML للطباعة
        _inc_rows_html = "".join(f"""<tr style="background:{'#eff6ff' if r[2]=='نتيجة' else '#f0fdf4' if r[2]=='صافي' else '#fff'}">
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;{'font-weight:700;' if r[2] in ('نتيجة','صافي','إجمالي') else ''}">{r[0]}</td>
          <td style="padding:10px 14px;border-bottom:1px solid #e2e8f0;text-align:left;font-family:monospace;{'font-weight:700;font-size:15px;' if r[2]=='صافي' else ''}{'color:#16a34a;' if r[2]=='صافي' and net_inc>=0 else 'color:#dc2626;' if r[2]=='صافي' and net_inc<0 else ''}">{f"{r[1]:,.2f} ر" if r[1]!="" else ""}</td>
        </tr>""" for r in income_rows)
        _inc_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;padding:30px;max-width:800px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}}.hdr p{{color:#64748b;font-size:11px;margin:2px 0;}}
.badge{{background:#1E3A8A;color:#fff;padding:5px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px 14px;text-align:right;}}
thead th:last-child{{text-align:left;}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px;}}
.sc{{background:#f1f5f9;border-radius:8px;padding:12px;text-align:center;border-top:3px solid #1E3A8A;}}
.sc .lbl{{font-size:10px;color:#94a3b8;}}.sc .val{{font-size:15px;font-weight:700;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}</style></head><body>
<div class="hdr"><div><h1>🏭 {FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
<div style="text-align:left"><div class="badge">قائمة الدخل</div><p style="color:#64748b;font-size:10px;margin-top:6px">من {ds_a} إلى {de_a}</p></div></div>
<table><thead><tr><th>البيان</th><th>المبلغ (ريال)</th></tr></thead><tbody>{_inc_rows_html}</tbody></table>
<div class="summary">
  <div class="sc"><div class="lbl">إجمالي المبيعات</div><div class="val">{sales_tot:,.2f} ر</div></div>
  <div class="sc"><div class="lbl">تكلفة البضاعة</div><div class="val">{cogs:,.2f} ر</div></div>
  <div class="sc" style="border-top-color:{'#16a34a' if net_inc>=0 else '#dc2626'}"><div class="lbl">صافي الربح</div><div class="val" style="color:{'#16a34a' if net_inc>=0 else '#dc2626'}">{net_inc:,.2f} ر</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_acc}</span></div>
</body></html>"""
        st.download_button("🖨️ طباعة قائمة الدخل (HTML)", _inc_html.encode('utf-8'),
            f"income_statement_{de_a}.html", "text/html; charset=utf-8", key="dl_inc_html")
        st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P")

    # ===== تبويب 2: التدفق النقدي =====
    with tabs[1]:
        st.markdown(f"#### قائمة التدفقات النقدية | من {ds_a} إلى {de_a}")
        # تحصيلات العملاء = دفعات مسجلة + مقدمات الطلبيات في الفترة
        ci_p_payments = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE payment_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        ci_p_advances  = float(run_query("SELECT COALESCE(SUM(advance_paid),0) as t FROM orders WHERE order_date BETWEEN :s AND :e AND advance_paid>0",{"s":ds_a,"e":de_a})['t'].iloc[0])
        ci_p = round(ci_p_payments + ci_p_advances, 2)
        sp_p = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE payment_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        sl_p = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        ex_p = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        # المشتريات الاستثمارية = ما دُفع فعلاً للموردين في الفترة
        pur_p = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE payment_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        # + المدفوعات النقدية المباشرة (نوع الدفع نقدي)
        pur_cash = float(run_query("SELECT COALESCE(SUM(p.total_price),0) as t FROM procurement p WHERE p.date BETWEEN :s AND :e AND NOT EXISTS (SELECT 1 FROM supplier_payments sp WHERE sp.procurement_id=p.id)",{"s":ds_a,"e":de_a})['t'].iloc[0])
        pur_p = round(pur_p + pur_cash, 2)
        op_cf = round(ci_p - sl_p - ex_p, 2)
        inv_cf= round(-pur_p, 2)
        fin_cf= round(-sp_p, 2)
        net_cf= round(op_cf + inv_cf + fin_cf, 2)
        cf_rows = [
            ("── أنشطة التشغيل (Operating)", "",         ""),
            ("تحصيلات من العملاء",              ci_p,      "+"),
            ("(–) رواتب مدفوعة",                sl_p,      "–"),
            ("(–) مصاريف تشغيلية",              ex_p,      "–"),
            ("◈ صافي التدفق التشغيلي",          op_cf,     "نتيجة"),
            ("── أنشطة الاستثمار (Investing)",  "",        ""),
            ("(–) مشتريات مواد خام",             pur_p,     "–"),
            ("◈ صافي التدفق الاستثماري",        inv_cf,    "نتيجة"),
            ("── أنشطة التمويل (Financing)",    "",        ""),
            ("(–) مدفوعات للموردين",             sp_p,      "–"),
            ("◈ صافي التدفق التمويلي",          fin_cf,    "نتيجة"),
            ("══ صافي التدفق النقدي الكلي",     net_cf,    "صافي"),
        ]
        cf_df = pd.DataFrame([(r[0], r[1] if r[1]!="" else float('nan')) for r in cf_rows], columns=["البيان","المبلغ (ريال)"])
        st.dataframe(cf_df, use_container_width=True, hide_index=True,
                     column_config={"المبلغ (ريال)": st.column_config.NumberColumn(format="%.2f ر")})
        f1,f2,f3 = st.columns(3)
        f1.metric("التدفق التشغيلي", f"{op_cf:,.2f} ر", delta="✅" if op_cf>=0 else "❌")
        f2.metric("التدفق الاستثماري", f"{inv_cf:,.2f} ر")
        f3.metric("صافي التدفق الكلي", f"{net_cf:,.2f} ر", delta="✅" if net_cf>=0 else "❌")
        st.download_button("⬇️ تنزيل CSV", df_to_csv(cf_df), "cashflow.csv", "text/csv")
        _cf_rows_html = "".join(f"""<tr style="background:{'#f8fafc' if r[2]=='' else '#eff6ff' if r[2]=='نتيجة' else '#fff'}">
          <td style="padding:9px 14px;border-bottom:1px solid #e2e8f0;{'font-weight:700;color:#1E3A8A;' if r[2]=='' else 'font-weight:700;' if r[2]=='نتيجة' else ''}">{r[0]}</td>
          <td style="padding:9px 14px;border-bottom:1px solid #e2e8f0;text-align:left;font-family:monospace;{'font-weight:700;' if r[2]=='نتيجة' else ''}{'color:#16a34a;' if r[2]=='نتيجة' and r[1]>=0 else 'color:#dc2626;' if r[2]=='نتيجة' and isinstance(r[1],float) and r[1]<0 else ''}">{f"{r[1]:,.2f} ر" if r[1]!="" else ""}</td>
        </tr>""" for r in cf_rows)
        _cf_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;padding:30px;max-width:800px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}}.badge{{background:#2563eb;color:#fff;padding:5px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px 14px;text-align:right;}}thead th:last-child{{text-align:left;}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px;}}
.sc{{background:#f1f5f9;border-radius:8px;padding:12px;text-align:center;border-top:3px solid #1E3A8A;}}
.sc .lbl{{font-size:10px;color:#94a3b8;}}.sc .val{{font-size:14px;font-weight:700;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}</style></head><body>
<div class="hdr"><div><h1>🏭 {FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
<div style="text-align:left"><div class="badge">قائمة التدفق النقدي</div><p style="color:#64748b;font-size:10px;margin-top:6px">من {ds_a} إلى {de_a}</p></div></div>
<table><thead><tr><th>البيان</th><th>المبلغ (ريال)</th></tr></thead><tbody>{_cf_rows_html}</tbody></table>
<div class="summary">
  <div class="sc"><div class="lbl">التدفق التشغيلي</div><div class="val" style="color:{'#16a34a' if op_cf>=0 else '#dc2626'}">{op_cf:,.2f} ر</div></div>
  <div class="sc"><div class="lbl">التدفق الاستثماري</div><div class="val" style="color:{'#16a34a' if inv_cf>=0 else '#dc2626'}">{inv_cf:,.2f} ر</div></div>
  <div class="sc"><div class="lbl">صافي التدفق الكلي</div><div class="val" style="color:{'#16a34a' if net_cf>=0 else '#dc2626'}">{net_cf:,.2f} ر</div></div>
</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_acc}</span></div>
</body></html>"""
        st.download_button("🖨️ طباعة التدفق النقدي (HTML)", _cf_html.encode('utf-8'),
            f"cashflow_{de_a}.html", "text/html; charset=utf-8", key="dl_cf_html")
        st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P")

    # ===== تبويب 3: الميزانية العمومية =====
    with tabs[2]:
        st.markdown(f"#### الميزانية العمومية (Balance Sheet) | بتاريخ {today_acc}")
        bal_rows = [
            ("══ الأصول المتداولة (Current Assets)",   "",          ""),
            ("النقدية والأرصدة",                        cash_bal,    "أصل"),
            ("المخزون (بالتكلفة)",                     inv_val,     "أصل"),
            ("ذمم مدينة (مستحق من العملاء)",            recv,        "أصل"),
            ("◈ إجمالي الأصول المتداولة",               total_assets,"إجمالي"),
            ("══ الخصوم المتداولة (Current Liabilities)","",         ""),
            ("ذمم دائنة (مستحق للموردين)",              sup_due,     "خصم"),
            ("◈ إجمالي الخصوم",                         total_liab,  "إجمالي"),
            ("══ حقوق الملكية (Equity)",                "",          ""),
            ("صافي حقوق الملكية",                       equity,      "حقوق"),
            ("══ إجمالي الخصوم + حقوق الملكية",        round(total_liab+equity,2), "تحقق"),
        ]
        bal_df = pd.DataFrame([(r[0], r[1] if r[1]!="" else float('nan')) for r in bal_rows], columns=["البيان","المبلغ (ريال)"])
        st.dataframe(bal_df, use_container_width=True, hide_index=True,
                     column_config={"المبلغ (ريال)": st.column_config.NumberColumn(format="%.2f ر")})
        b1,b2,b3 = st.columns(3)
        b1.metric("إجمالي الأصول",     f"{total_assets:,.2f} ر")
        b2.metric("إجمالي الخصوم",     f"{total_liab:,.2f} ر")
        b3.metric("حقوق الملكية",       f"{equity:,.2f} ر", delta="✅" if equity>=0 else "⚠️")
        if abs(total_assets - (total_liab + equity)) < 1:
            st.success("✅ الميزانية متوازنة — الأصول = الخصوم + حقوق الملكية")
        else:
            st.warning(f"⚠️ فرق في التوازن: {abs(total_assets-(total_liab+equity)):,.2f} ر")
        st.download_button("⬇️ تنزيل CSV", df_to_csv(bal_df), "balance_sheet.csv", "text/csv")
        _bal_rows_html = "".join(f"""<tr style="background:{'#f8fafc' if r[2]=='' else '#eff6ff' if r[2]=='إجمالي' else '#f0fdf4' if r[2]=='حقوق' else '#fff'}">
          <td style="padding:9px 14px;border-bottom:1px solid #e2e8f0;{'font-weight:700;color:#1E3A8A;' if r[2]=='' else 'font-weight:700;' if r[2] in ('إجمالي','حقوق','تحقق') else ''}">{r[0]}</td>
          <td style="padding:9px 14px;border-bottom:1px solid #e2e8f0;text-align:left;font-family:monospace;font-weight:{'700' if r[2] in ('إجمالي','حقوق','تحقق') else '400'}">{f"{r[1]:,.2f} ر" if r[1]!="" else ""}</td>
        </tr>""" for r in bal_rows)
        _check = "✅ الميزانية متوازنة" if abs(total_assets-(total_liab+equity))<1 else "⚠️ تحقق من الأرقام"
        _bal_html = f"""<!DOCTYPE html><html dir="rtl" lang="ar"><head><meta charset="UTF-8">
<style>@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
*{{box-sizing:border-box;margin:0;padding:0;}}body{{font-family:'Cairo',sans-serif;direction:rtl;background:#fff;color:#1e293b;padding:30px;max-width:800px;margin:0 auto;}}
.hdr{{display:flex;justify-content:space-between;align-items:center;border-bottom:4px solid #1E3A8A;padding-bottom:12px;margin-bottom:20px;}}
.hdr h1{{color:#1E3A8A;font-size:18px;font-weight:800;}}.badge{{background:#7c3aed;color:#fff;padding:5px 16px;border-radius:20px;font-size:13px;font-weight:700;}}
table{{width:100%;border-collapse:collapse;margin-bottom:20px;}}
thead th{{background:#1E3A8A;color:#fff;padding:10px 14px;text-align:right;}}thead th:last-child{{text-align:left;}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px;}}
.sc{{background:#f1f5f9;border-radius:8px;padding:12px;text-align:center;border-top:3px solid #1E3A8A;}}
.sc .lbl{{font-size:10px;color:#94a3b8;}}.sc .val{{font-size:14px;font-weight:700;}}
.check{{background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:10px;text-align:center;font-weight:700;color:#16a34a;margin-top:10px;}}
.footer{{margin-top:20px;border-top:1px solid #e2e8f0;padding-top:10px;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8;}}
@media print{{body{{padding:15px;}}}}</style></head><body>
<div class="hdr"><div><h1>🏭 {FACTORY_NAME}</h1><p>{FACTORY_ADDRESS}</p></div>
<div style="text-align:left"><div class="badge">الميزانية العمومية</div><p style="color:#64748b;font-size:10px;margin-top:6px">بتاريخ {today_acc}</p></div></div>
<table><thead><tr><th>البيان</th><th>المبلغ (ريال)</th></tr></thead><tbody>{_bal_rows_html}</tbody></table>
<div class="summary">
  <div class="sc"><div class="lbl">إجمالي الأصول</div><div class="val">{total_assets:,.2f} ر</div></div>
  <div class="sc"><div class="lbl">إجمالي الخصوم</div><div class="val">{total_liab:,.2f} ر</div></div>
  <div class="sc" style="border-top-color:#7c3aed"><div class="lbl">حقوق الملكية</div><div class="val" style="color:#7c3aed">{equity:,.2f} ر</div></div>
</div>
<div class="check">{_check} — الأصول = الخصوم + حقوق الملكية</div>
<div class="footer"><span>🏭 {FACTORY_NAME} — {FACTORY_ADDRESS}</span><span>نظام ERP v7.0 | {today_acc}</span></div>
</body></html>"""
        st.download_button("🖨️ طباعة الميزانية العمومية (HTML)", _bal_html.encode('utf-8'),
            f"balance_sheet_{today_acc.replace('/','')}.html", "text/html; charset=utf-8", key="dl_bal_html")
        st.caption("💡 افتح في Chrome أو Safari ثم Ctrl+P")

# ==========================================
# [8] الاستعلام المتقدم
# ==========================================
elif menu == "🔍 الاستعلام المتقدم":
    st.subheader("🔍 مركز الاستعلام")
    qt = st.selectbox("نوع الاستعلام:", ["عميل","طلبية","مورد","خزان بالرقم المسلسل","فاتورة"])
    cdf6 = run_query("SELECT id,trade_name FROM customers ORDER BY trade_name")
    sdf4 = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
    odf5 = run_query("SELECT order_id FROM orders ORDER BY order_date DESC")
    if qt=="عميل":
        sc6 = st.selectbox("العميل:", ["الكل"]+(cdf6['trade_name'].tolist() if not cdf6.empty else []))
        if st.button("🔍 بحث"):
            df = run_query("SELECT trade_name,cr_number,tax_number FROM customers") if sc6=="الكل" else run_query("SELECT * FROM customers WHERE trade_name=:n",{"n":sc6})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)
            if not df.empty: st.download_button("⬇️ تنزيل",df_to_csv(df),"customers.csv","text/csv")
    elif qt=="طلبية":
        so5 = st.selectbox("الطلبية:", ["الكل"]+(odf5['order_id'].tolist() if not odf5.empty else []))
        if st.button("🔍 بحث"):
            df = run_query("SELECT o.order_id,c.trade_name,o.qty,o.total_price,o.status,o.order_date FROM orders o JOIN customers c ON o.customer_id=c.id ORDER BY o.order_date DESC") if so5=="الكل" else run_query("SELECT o.order_id,c.trade_name,o.qty,o.total_price,o.status,o.order_date FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.order_id=:oid",{"oid":so5})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)
            if not df.empty: st.download_button("⬇️ تنزيل",df_to_csv(df),"orders.csv","text/csv")
    elif qt=="مورد":
        ss4 = st.selectbox("المورد:", ["الكل"]+(sdf4['original_name'].tolist() if not sdf4.empty else []))
        if st.button("🔍 بحث"):
            df = run_query("SELECT s.original_name,p.date,p.material_name,p.quantity,p.total_price FROM procurement p JOIN suppliers s ON p.supplier_id=s.id ORDER BY p.date DESC") if ss4=="الكل" else run_query("SELECT date,material_name,quantity,unit_price,total_price FROM procurement WHERE supplier_id=:sid ORDER BY date DESC",{"sid":int(sdf4[sdf4['original_name']==ss4]['id'].iloc[0])})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)
            if not df.empty: st.download_button("⬇️ تنزيل",df_to_csv(df),"proc.csv","text/csv")
    elif qt=="خزان بالرقم المسلسل":
        sn = st.text_input("الرقم المسلسل:")
        if st.button("🔍 بحث") and sn:
            df = run_query("SELECT serial_number,order_id,prod_date,supervisor FROM production_tanks WHERE serial_number ILIKE :s",{"s":f"%{sn}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)
    elif qt=="فاتورة":
        iid = st.number_input("رقم الفاتورة:", min_value=1, value=1)
        if st.button("🔍 بحث"):
            df = run_query("SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,si.grand_total,si.net_required FROM sales_invoices si JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id WHERE si.invoice_id=:iid",{"iid":iid})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)
            if not df.empty: st.download_button("⬇️ تنزيل",df_to_csv(df),f"inv_{iid}.csv","text/csv")

# ==========================================
# [9] حذف كامل
# ==========================================
elif menu == "🗑️ حذف كامل للبيانات":
    st.subheader("🗑️ حذف كامل")
    st.error("⚠️ تحذير شديد: هذه العملية تحذف جميع البيانات نهائياً!")
    cf = st.radio("هل أنت متأكد؟", ["لا، إلغاء","نعم، أريد الحذف الكامل"])
    if cf == "نعم، أريد الحذف الكامل":
        st.warning("⚠️ آخر تحذير!")
        if st.button("🗑️ تأكيد الحذف الكامل — لا رجعة"):
            for t in ["sales_invoices","customer_payments","supplier_payments","delivery_orders","production_tanks","production_days","general_expenses","worker_salaries","worker_advances","workers","procurement","orders","customers","suppliers"]:
                run_write(f"DELETE FROM {t}")
            run_write("UPDATE inventory SET quantity=0.0")
            # تصفير كامل لـ session_state حتى لا تظهر بيانات قديمة
            keys_to_clear = [k for k in st.session_state.keys()]
            for k in keys_to_clear:
                del st.session_state[k]
            st.success("✅ تم حذف جميع البيانات وتصفير الجلسة!"); st.balloons()
            st.rerun()
    else:
        st.info("✅ العملية ملغاة.")
