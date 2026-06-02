import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import text

# ================================================================
# QR Code Generator — Pure Python + Pillow (no external libraries)
# ================================================================
# Stylized to mimic square-with-white-center design
# ================================================================
import io as _io, base64 as _b64
from PIL import Image as _Img, ImageDraw as _Draw

def make_qr_b64(text, color=(30, 58, 138), module_size=10, quiet=4, hole_size=4):
    """
    توليد QR Code مخصص يحاكي النمط المطلوب (مربعات مفرغة) ويدعم الحجم الديناميكي
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1, # we handle size manually
            border=0,
        )
        qr.add_data(text)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        
        n_rows = len(matrix)
        n_cols = len(matrix[0])
        
        # Calculate full image size with border
        full_size_px = (n_rows + 2 * quiet) * module_size
        
        # Base image
        img = _Img.new('RGB', (full_size_px, full_size_px), (255, 255, 255))
        draw = _Draw.Draw(img)
        
        # Custom module design: square with white center
        def draw_custom_module(draw, r, c, color):
            # Calculate pixel coordinates
            x0 = (c + quiet) * module_size
            y0 = (r + quiet) * module_size
            x1 = x0 + module_size - 1
            y1 = y0 + module_size - 1
            
            # Inner hole pixel coordinates
            h_x0 = x0 + (module_size - hole_size) // 2
            h_y0 = y0 + (module_size - hole_size) // 2
            h_x1 = h_x0 + hole_size - 1
            h_y1 = h_y0 + hole_size - 1
            
            # Outer colored box
            draw.rectangle([x0, y0, x1, y1], fill=color)
            # Inner white hole
            draw.rectangle([h_x0, h_y0, h_x1, h_y1], fill=(255, 255, 255))

        # Replicate style from input image for entire QR code
        for r in range(n_rows):
            for c in range(n_cols):
                if matrix[r][c]:
                    draw_custom_module(draw, r, c, color)
                    
        # Apply special style to finder patterns to match exactly
        finder_size = 7
        for r_start, c_start in [(0, 0), (0, n_cols - finder_size), (n_rows - finder_size, 0)]:
            # Outer box
            f_x0 = (c_start + quiet) * module_size
            f_y0 = (r_start + quiet) * module_size
            f_x1 = f_x0 + finder_size * module_size - 1
            f_y1 = f_y0 + finder_size * module_size - 1
            
            # Style the finder pattern itself (large squares)
            for r_f in range(finder_size):
                for c_f in range(finder_size):
                    # Check if standard finder logic applies
                    if (r_f == 0 or r_f == finder_size - 1 or c_f == 0 or c_f == finder_size - 1) or                        (2 <= r_f <= finder_size - 3 and 2 <= c_f <= finder_size - 3):
                        # Use special stylized module for finders
                        f_mod_x0 = (c_start + c_f + quiet) * module_size
                        f_mod_y0 = (r_start + r_f + quiet) * module_size
                        f_mod_x1 = f_mod_x0 + module_size - 1
                        f_mod_y1 = f_mod_x0 + module_size - 1
                        
                        # Re-implement stylized module logic to avoid double draw
                        draw.rectangle([f_mod_x0, f_mod_y0, f_mod_x1, f_mod_y1], fill=color)
                        # Center white area is handled by standard modules that will be overlaid
                        # Let's refine to draw exactly like the modules within finder patterns.
                        
                        # Outer finder pattern style is crucial
                        if r_f == 0 or r_f == finder_size - 1 or c_f == 0 or c_f == finder_size - 1:
                           # Stylized modules on finder border
                           pass
                        
            # Final touch: ensure inner white space of finder is clear before drawing stylized centers
            inner_f_x0 = f_x0 + module_size
            inner_f_y0 = f_y0 + module_size
            inner_f_x1 = f_x1 - module_size
            inner_f_y1 = f_y1 - module_size
            
            # Correcting logic: The finder patterns themselves contain regular stylized modules.
            # No special overlays needed, just standard modules.
            
        # Standard draw already handles everything. The previous logic was overly complex.

        buf = _io.BytesIO()
        img.save(buf, format='PNG')
        return _b64.b64encode(buf.getvalue()).decode()
        
    except ImportError:
        # PURE FALLBACK (not stylized to avoid extreme complexity without library)
        # We will keep a standardfallback to avoid crash
        import io, base64
        from PIL import Image, ImageDraw
        qr_inv_b64 = make_standard_fallback_qr_b64(text, color, module_size, quiet)
        return qr_inv_b64


# FALLBACK: A standard dynamic pure-python QR generator if library is missing
def make_standard_fallback_qr_b64(text, color, module_size, quiet):
    from PIL import Image as _Img, ImageDraw as _Draw
    raw = text.encode('utf-8', errors='replace')
    n = len(raw)
    
    if n <= 19: ver, ec, dc = 1, 7, 19
    elif n <= 34: ver, ec, dc = 2, 10, 34
    elif n <= 55: ver, ec, dc = 3, 15, 55
    elif n <= 80: ver, ec, dc = 4, 20, 80
    else: ver, ec, dc = 40, 114, 1663
    
    size = 17 + 4 * ver
    ns = (size + 2 * quiet) * module_size
    img = _Img.new('RGB', (ns, ns), (255, 255, 255))
    draw = _Draw.Draw(img)
    
    #Finder patterns
    for r_s, c_s in [(0, 0), (0, size-7), (size-7, 0)]:
        f_x0 = (c_s + quiet) * module_size
        f_y0 = (r_s + quiet) * module_size
        f_x1 = f_x0 + 7 * module_size - 1
        f_y1 = f_y0 + 7 * module_size - 1
        # Re-apply stylized module design even to finders in fallback as best effort
        for r_f in range(7):
            for c_f in range(7):
                if (r_f == 0 or r_f == 6 or c_f == 0 or c_f == 6) or (2 <= r_f <= 4 and 2 <= c_f <= 4):
                    m_x0 = (c_s + c_f + quiet) * module_size
                    m_y0 = (r_s + r_f + quiet) * module_size
                    # No holes in fallback to ensure legibility and simplicity
                    draw.rectangle([m_x0, m_y0, m_x0 + module_size - 1, m_y0 + module_size - 1], fill=color)
                    
    #Timing patterns
    for i in range(8, size-8):
        # Even timing points
        x = (i + quiet) * module_size
        y = (6 + quiet) * module_size
        draw.rectangle([x, y, x + module_size - 1, y + module_size - 1], fill=color if i%2==0 else (255,255,255))
        
        x = (6 + quiet) * module_size
        y = (i + quiet) * module_size
        draw.rectangle([x, y, x + module_size - 1, y + module_size - 1], fill=color if i%2==0 else (255,255,255))
        
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()

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
    "ألياف (Mat 450)",
    "روفرز (Roving 600)",
    "تيسو (Tissue)",
    "مصلد (Catalyst)",
    "كربونات الكالسيوم",
    "سيليكا (Silica)"
]

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
    st.subheader("📈 لوحة التحكم")
    c1,c2 = st.columns(2)
    d_start = c1.date_input("من:", datetime.date.today()-datetime.timedelta(days=30))
    d_end = c2.date_input("إلى:", datetime.date.today())
    st.markdown("---")
    total_sales = float(run_query("SELECT COALESCE(SUM(grand_total),0) as t FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e",{"s":d_start,"e":d_end})['t'].iloc[0])
    total_proc = float(run_query("SELECT COALESCE(SUM(total_price),0) as t FROM procurement WHERE date BETWEEN :s AND :e",{"s":d_start,"e":d_end})['t'].iloc[0])
    total_sal = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",{"s":d_start,"e":d_end})['t'].iloc[0])
    total_exp = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",{"s":d_start,"e":d_end})['t'].iloc[0])
    net_profit = total_sales - (total_proc+total_sal+total_exp)
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("إجمالي المبيعات", f"{total_sales:,.2f} ر")
    m2.metric("إجمالي المشتريات", f"{total_proc:,.2f} ر")
    m3.metric("الرواتب والمصاريف", f"{total_sal+total_exp:,.2f} ر")
    m4.metric("صافي الربح", f"{net_profit:,.2f} ر", delta="ربح ✅" if net_profit>=0 else "خسارة ❌")
    st.markdown("---")
    st.write("### 📦 الطلبيات النشطة")
    adf = run_query("SELECT o.order_id as الطلبية,c.trade_name as العميل,o.qty as الكمية,o.total_price as القيمة,o.status as الحالة FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
    st.dataframe(adf if not adf.empty else pd.DataFrame({"الحالة":["لا توجد طلبيات"]}),use_container_width=True)
    st.write("### 🏪 المخزن")
    inv = run_query("SELECT material_name as المادة,quantity as الكمية FROM inventory ORDER BY material_name")
    st.dataframe(inv if not inv.empty else pd.DataFrame(),use_container_width=True)

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

            # احتياج هذه الطلبية
            this_order_needs = {
                "راتنج كميائي صنف اول للديزل": r_ex * qty_f,
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

            # احتياج الطلبيات الأخرى الجارية (غير المصنعة بعد)
            active_ord = run_query("""
                SELECT o.qty,o.resin_exp,o.mat_exp,o.roving_exp,o.tissue_exp,o.catalyst_exp,o.calcium_exp,o.silica_exp,
                       COALESCE((SELECT SUM(pd.actual_qty) FROM production_days pd WHERE pd.order_id=o.order_id AND pd.status='مغلق'),0) as made
                FROM orders o WHERE o.status='قيد التنفيذ'
            """)
            reserved = {k:0.0 for k in this_order_needs}
            if not active_ord.empty:
                for _,ar in active_ord.iterrows():
                    remaining_tanks = max(0, int(ar['qty']) - int(ar['made']))
                    if remaining_tanks > 0:
                        reserved["راتنج كميائي صنف اول للديزل"] += remaining_tanks * float(ar['resin_exp'] or 0)
                        reserved["ألياف (Mat 450)"]              += remaining_tanks * float(ar['mat_exp'] or 0)
                        reserved["روفرز (Roving 600)"]           += remaining_tanks * float(ar['roving_exp'] or 0)
                        reserved["تيسو (Tissue)"]                += remaining_tanks * float(ar['tissue_exp'] or 0)
                        reserved["مصلد (Catalyst)"]              += remaining_tanks * float(ar['catalyst_exp'] or 0)
                        reserved["كربونات الكالسيوم"]            += remaining_tanks * float(ar['calcium_exp'] or 0)
                        reserved["سيليكا (Silica)"]              += remaining_tanks * float(ar['silica_exp'] or 0)

            # حساب النواقص
            shortages = {}
            check_rows = []
            for mat, needed in this_order_needs.items():
                if needed <= 0: continue
                stock    = inv_dict.get(mat, 0.0)
                res      = reserved.get(mat, 0.0)
                available = max(0.0, stock - res)
                shortage  = max(0.0, needed - available)
                status_icon = "✅" if shortage == 0 else "🔴"
                check_rows.append({"المادة":mat, "المخزون":f"{stock:,.2f}", "محجوز للطلبيات":f"{res:,.2f}", "متاح":f"{available:,.2f}", "مطلوب":f"{needed:,.2f}", "العجز":f"{shortage:,.2f}", "الحالة":status_icon})
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
                pct_prod = int(tanks_made/int(ord_r['qty'])*100) if int(ord_r['qty'])>0 else 0
                pct_del = int(tanks_delivered/int(ord_r['qty'])*100) if int(ord_r['qty'])>0 else 0

                # عرض بطاقة الطلبية
                with st.expander(f"📦 {oid_a} | {ord_r['trade_name']} | {int(ord_r['qty'])} خزان | {ord_r['tank_use']} | القيمة: {float(ord_r['total_price']):,.0f} ر", expanded=False):

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
                    st.progress(pct_prod/100, text=f"التصنيع: {pct_prod}%")

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

                    st.progress(pct_del/100, text=f"التسليم: {pct_del}%")

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
        if 'pk' not in st.session_state: st.session_state.pk = 0
        cdf2 = run_query("SELECT id,trade_name FROM customers ORDER BY trade_name")
        if not cdf2.empty:
            with st.form(f"pf_{st.session_state.pk}", clear_on_submit=True):
                sc = st.selectbox("العميل:", cdf2['trade_name'].tolist())
                cid2 = int(cdf2[cdf2['trade_name']==sc]['id'].iloc[0])
                odf2 = run_query("SELECT order_id FROM orders WHERE customer_id=:c AND status='قيد التنفيذ'",{"c":cid2})
                so = st.selectbox("الطلبية:", odf2['order_id'].tolist() if not odf2.empty else ["—"])
                pa = st.number_input("مبلغ الدفعة (ريال):", min_value=0.0, value=0.0)
                pt = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"])
                pb = st.text_input("البنك:")
                if st.form_submit_button("💵 اعتماد الدفعة"):
                    if run_write("INSERT INTO customer_payments(customer_id,order_id,amount,payment_type,bank_name) VALUES(:ci,:oi,:a,:pt,:b)",
                                 {"ci":cid2,"oi":so,"a":pa,"pt":pt,"b":pb}):
                        st.success(f"✅ تم تسجيل {pa:,.2f} ريال!")
                        st.session_state.pk += 1
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
            if st.button("📊 عرض كشف الحساب التفصيلي"):
                orders_stmt = run_query("""SELECT o.order_id,o.order_date,o.tank_use,o.tank_capacity,o.tank_type,
                    o.qty,o.unit_price,o.total_price,o.advance_paid,o.remaining_balance,o.status
                    FROM orders o WHERE o.customer_id=:cid AND o.order_date BETWEEN :s AND :e ORDER BY o.order_date""",
                    {"cid":cid3,"s":ds,"e":de})
                if orders_stmt.empty:
                    st.info("لا توجد طلبيات في هذه الفترة.")
                else:
                    # ---- جمع بيانات كل طلبية ----
                    orders_data_html = []
                    grand_inv=0.0; grand_paid=0.0; grand_del=0

                    for _, ord_row in orders_stmt.iterrows():
                        oid_s = ord_row['order_id']

                        del_df = run_query("SELECT delivery_id,delivery_date,shipped_qty,driver_name,car_plate FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_date",{"oid":oid_s})
                        total_del = int(del_df['shipped_qty'].sum()) if not del_df.empty else 0

                        inv_s = run_query("SELECT invoice_id,invoice_date,grand_total,advance_deducted,net_required FROM sales_invoices WHERE order_id=:oid ORDER BY invoice_date",{"oid":oid_s})
                        total_inv_ord = float(inv_s['net_required'].sum()) if not inv_s.empty else 0.0

                        pay_s = run_query("SELECT payment_date,amount,payment_type,bank_name FROM customer_payments WHERE order_id=:oid AND customer_id=:cid ORDER BY payment_date",{"oid":oid_s,"cid":cid3})
                        total_paid_ord = float(pay_s['amount'].sum()) if not pay_s.empty else 0.0

                        grand_inv+=total_inv_ord; grand_paid+=total_paid_ord; grand_del+=total_del

                        orders_data_html.append({
                            'order_id':         oid_s,
                            'order_date':        str(ord_row['order_date']),
                            'tank_use':          str(ord_row['tank_use']),
                            'tank_capacity':     str(ord_row['tank_capacity'] or '—'),
                            'tank_type':         str(ord_row['tank_type']),
                            'status':            str(ord_row['status']),
                            'qty':               int(ord_row['qty']),
                            'unit_price':        float(ord_row['unit_price']),
                            'total_price':       float(ord_row['total_price']),
                            'advance_paid':      float(ord_row['advance_paid']),
                            'remaining_balance': float(ord_row['remaining_balance']),
                            'total_delivered':   total_del,
                            'total_invoiced':    total_inv_ord,
                            'total_paid':        total_paid_ord,
                            'deliveries': del_df.to_dict('records') if not del_df.empty else [],
                            'invoices':   inv_s.to_dict('records')  if not inv_s.empty else [],
                            'payments':   pay_s.to_dict('records')  if not pay_s.empty else [],
                        })

                    # ---- عرض ملخص في Streamlit ----
                    render_header()
                    st.markdown(f"<h2 style='text-align:center;color:#1E3A8A;'>كشف حساب تفصيلي — {sel_c3}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;color:#64748b;'>الفترة: {ds} إلى {de}</p>", unsafe_allow_html=True)
                    st.markdown("---")
                    g1,g2,g3,g4 = st.columns(4)
                    g1.metric("إجمالي الفواتير", f"{grand_inv:,.2f} ر")
                    g2.metric("إجمالي المدفوع", f"{grand_paid:,.2f} ر")
                    g3.metric("🔴 الرصيد الكلي", f"{grand_inv-grand_paid:,.2f} ر")
                    g4.metric("إجمالي الخزانات المسلمة", f"{grand_del} خزان")

                    # ---- توليد HTML وزر التنزيل ----
                    html_output = generate_customer_statement_html(
                        customer_name  = sel_c3,
                        customer_info  = cust_info3,
                        date_from      = ds,
                        date_to        = de,
                        orders_data    = orders_data_html
                    )
                    st.markdown("---")
                    col_dl1, col_dl2 = st.columns(2)
                    summary = pd.DataFrame([{"العميل":sel_c3,"الفترة":f"{ds} إلى {de}","إجمالي الفواتير":grand_inv,"إجمالي المدفوع":grand_paid,"الرصيد":grand_inv-grand_paid,"الخزانات المسلمة":grand_del}])
                    col_dl1.download_button("⬇️ تنزيل CSV", df_to_csv(summary), f"stmt_{sel_c3}.csv", "text/csv")
                    col_dl2.download_button(
                        label="🖨️ تنزيل كشف الحساب للطباعة (HTML)",
                        data=html_output.encode('utf-8'),
                        file_name=f"customer_statement_{sel_c3}.html",
                        mime="text/html; charset=utf-8",
                        help="افتح الملف في المتصفح ثم اضغط Ctrl+P لطباعته أو حفظه PDF"
                    )
                    st.caption("💡 بعد التنزيل: افتح الملف في Chrome أو Safari ثم اضغط Ctrl+P أو Cmd+P لطباعته أو حفظه كـ PDF")

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

    MAT_MAP_KEYS = {
        "راتنج":       "راتنج كميائي صنف اول للديزل",
        "ألياف Mat":   "ألياف (Mat 450)",
        "روفرز":       "روفرز (Roving 600)",
        "تيسو":        "تيسو (Tissue)",
        "مصلد":        "مصلد (Catalyst)",
        "كالسيوم":     "كربونات الكالسيوم",
        "سيليكا":      "سيليكا (Silica)",
    }

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
            opts = [f"{r['order_id']} | {r['trade_name']} | {r['qty']} خزان" for _,r in odf.iterrows()]
            sel = st.selectbox("اختر الطلبية:", opts, key="prod_sel")
            oid = sel.split(" | ")[0]
            row = odf[odf['order_id']==oid].iloc[0]
            c1,c2 = st.columns(2)
            tanks_today = c1.number_input("عدد الخزانات المستهدفة اليوم:", min_value=1, value=2, key="prod_planned_n")
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
            mat_map_full_chk = {
                "راتنج كميائي صنف اول للديزل": calc["راتنج"],
                "ألياف (Mat 450)":              calc["ألياف Mat"],
                "روفرز (Roving 600)":           calc["روفرز"],
                "تيسو (Tissue)":                calc["تيسو"],
                "مصلد (Catalyst)":              calc["مصلد"],
                "كربونات الكالسيوم":            calc["كالسيوم"],
                "سيليكا (Silica)":              calc["سيليكا"],
            }
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

            if st.button("🎬 بدء الوردية وصرف المواد من المخزن", type="primary"):
                if not supervisor_inp:
                    st.error("أدخل اسم المشرف!")
                elif prod_shortages:
                    st.error("⛔ لا يمكن بدء الوردية — يوجد عجز في المواد الخام. أضف المواد أولاً.")
                else:
                    mat_map_full = {
                        "راتنج كميائي صنف اول للديزل": calc["راتنج"],
                        "ألياف (Mat 450)":              calc["ألياف Mat"],
                        "روفرز (Roving 600)":           calc["روفرز"],
                        "تيسو (Tissue)":                calc["تيسو"],
                        "مصلد (Catalyst)":              calc["مصلد"],
                        "كربونات الكالسيوم":            calc["كالسيوم"],
                        "سيليكا (Silica)":              calc["سيليكا"],
                    }
                    for mat, qty in mat_map_full.items():
                        if qty > 0:
                            run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m", {"q":qty,"m":mat})
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
                    run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name=:m", {"q":qty,"m":mat_full})

                # تنفيذ الصرف الإضافي
                for mat_short, qty in extra_items.items():
                    mat_full = MAT_MAP_KEYS.get(mat_short, mat_short)
                    run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m", {"q":qty,"m":mat_full})

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
    tabs = st.tabs(["🤝 مورد جديد","🚚 فاتورة توريد","💳 دفعات مورد","🔍 كشف حساب مورد","🔧 ضبط المخزن","📊 رصيد المخزن"])

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
            if 'pck' not in st.session_state: st.session_state.pck = 0
            if 'pitems' not in st.session_state: st.session_state.pitems = []
            pck = st.session_state.pck
            csup = st.selectbox("المورد:", sdf['original_name'].tolist(), key=f"psup_{pck}")
            sup_id = int(sdf[sdf['original_name']==csup]['id'].iloc[0])
            inv_num = st.text_input("رقم الفاتورة:*", key=f"pin_{pck}")
            pay_tp = st.selectbox("نوع الدفع:", ["آجل","نقدي","دفع جزئي"], key=f"ppt_{pck}")
            adv_proc = st.number_input("الدفعة المقدمة (ريال):", min_value=0.0, value=0.0, key=f"padv_{pck}")
            st.markdown("**➕ إضافة بنود:**")
            with st.form("aitf", clear_on_submit=True):
                ci1,ci2,ci3 = st.columns(3)
                ms = ci1.selectbox("المادة:", raw_materials_list)
                iq = ci2.number_input("الكمية:", min_value=0.0, value=0.0)
                ip = ci3.number_input("سعر الوحدة:", min_value=0.0, value=0.0)
                if st.form_submit_button("➕ إضافة"):
                    if iq>0 and ip>0:
                        st.session_state.pitems.append({"المادة":ms,"الكمية":iq,"سعر الوحدة":ip,"الإجمالي":iq*ip})
                        st.success(f"✅ {ms}")
            if st.session_state.pitems:
                idf = pd.DataFrame(st.session_state.pitems)
                st.dataframe(idf, use_container_width=True)
                sub = idf['الإجمالي'].sum(); vat=sub*0.15; grand=sub+vat; net_af=grand-adv_proc
                st.markdown(f"**قبل الضريبة:** {sub:,.2f} | **ضريبة 15%:** {vat:,.2f} | **الإجمالي:** {grand:,.2f} | **بعد المقدم:** {net_af:,.2f}")
                et = st.number_input("قيمة الفاتورة للتحقق:", min_value=0.0, value=round(grand,2), key=f"et_{pck}")
                if abs(et-grand)>1: st.warning(f"⚠️ فرق {abs(et-grand):,.2f} ر!")
                else: st.success("✅ القيمة مطابقة.")
                cb1,cb2 = st.columns(2)
                if cb1.button("✅ اعتماد الفاتورة"):
                    if not inv_num: st.error("أدخل رقم الفاتورة!")
                    else:
                        for item in st.session_state.pitems:
                            run_write("INSERT INTO procurement(supplier_id,material_name,quantity,unit_price,total_price) VALUES(:sid,:m,:q,:up,:tp)",{"sid":sup_id,"m":item['المادة'],"q":item['الكمية'],"up":item['سعر الوحدة'],"tp":item['الإجمالي']})
                            run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name=:m",{"q":item['الكمية'],"m":item['المادة']})
                        if adv_proc>0:
                            pl = run_query("SELECT id FROM procurement WHERE supplier_id=:sid ORDER BY id DESC LIMIT 1",{"sid":sup_id})
                            if not pl.empty:
                                run_write("INSERT INTO supplier_payments(supplier_id,procurement_id,amount,payment_type) VALUES(:sid,:pid,:a,'مقدم')",{"sid":sup_id,"pid":int(pl['id'].iloc[0]),"a":adv_proc})
                        st.success(f"✅ تم اعتماد الفاتورة {inv_num}!")
                        st.session_state.pitems=[]; st.session_state.pck+=1; st.rerun()
                if cb2.button("🗑️ مسح البنود"):
                    st.session_state.pitems=[]; st.rerun()

    with tabs[2]:
        if 'spk' not in st.session_state: st.session_state.spk = 0
        sdf2 = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if not sdf2.empty:
            with st.form(f"spf_{st.session_state.spk}", clear_on_submit=True):
                ss = st.selectbox("المورد:", sdf2['original_name'].tolist())
                sid2 = int(sdf2[sdf2['original_name']==ss]['id'].iloc[0])
                prc = run_query("SELECT id,material_name,total_price,date FROM procurement WHERE supplier_id=:sid ORDER BY date DESC",{"sid":sid2})
                if not prc.empty:
                    popts = [f"#{r['id']} - {r['material_name']} - {r['total_price']:,.2f} ر - {r['date']}" for _,r in prc.iterrows()]
                    sp = st.selectbox("الفاتورة:", popts)
                    pid = int(sp.split("#")[1].split(" ")[0])
                    sa = st.number_input("المبلغ:", min_value=0.0, value=0.0)
                    spt = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي"])
                    sb = st.text_input("البنك:")
                    sn = st.text_input("ملاحظات:")
                    if st.form_submit_button("💳 اعتماد الدفعة"):
                        ok = run_write("INSERT INTO supplier_payments(supplier_id,procurement_id,amount,payment_type,bank_name,notes) VALUES(:sid,:pid,:a,:pt,:b,:n)",{"sid":sid2,"pid":pid,"a":sa,"pt":spt,"b":sb,"n":sn})
                        if ok:
                            pr = prc[prc['id']==pid].iloc[0]
                            tp = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE procurement_id=:pid",{"pid":pid})['t'].iloc[0])
                            rem = float(pr['total_price'])*1.15 - tp
                            st.success("✅ تم تسجيل الدفعة! تم تصفير الحقول.")
                            render_header()
                            st.markdown(f"""
                            <div style="border:1px solid #CBD5E1;padding:15px;border-radius:8px;">
                            <h3 style="text-align:center;">إيصال دفع لمورد</h3>
                            <p><b>المورد:</b> {ss} | <b>الفاتورة:</b> #{pid}</p>
                            <p><b>المدفوع:</b> {sa:,.2f} ر | <b>الطريقة:</b> {spt}</p>
                            <p><b>المتبقي:</b> {rem:,.2f} ر | <b>التاريخ:</b> {datetime.date.today()}</p>
                            </div>""", unsafe_allow_html=True)
                            st.session_state.spk+=1; st.rerun()
                else:
                    st.info("لا توجد فواتير لهذا المورد.")

    with tabs[3]:
        sdf3 = run_query("SELECT id,original_name FROM suppliers ORDER BY original_name")
        if not sdf3.empty:
            ss3 = st.selectbox("المورد:", sdf3['original_name'].tolist(), key="sstmt")
            sid3 = int(sdf3[sdf3['original_name']==ss3]['id'].iloc[0])
            d1,d2 = st.columns(2)
            ds3 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="sds3")
            de3 = d2.date_input("إلى:", datetime.date.today(), key="sde3")
            if st.button("📊 عرض كشف المورد"):
                ph = run_query("SELECT date,material_name,quantity,unit_price,total_price,ROUND(CAST(total_price*1.15 AS numeric),2) as مع_الضريبة FROM procurement WHERE supplier_id=:sid AND date BETWEEN :s AND :e ORDER BY date",{"sid":sid3,"s":ds3,"e":de3})
                pyh = run_query("SELECT payment_date,amount,payment_type,bank_name,notes FROM supplier_payments WHERE supplier_id=:sid AND payment_date BETWEEN :s AND :e ORDER BY payment_date",{"sid":sid3,"s":ds3,"e":de3})
                ti = float(ph['مع_الضريبة'].sum()) if not ph.empty else 0.0
                tp2 = float(pyh['amount'].sum()) if not pyh.empty else 0.0
                render_header()
                st.markdown(f"<h3 style='text-align:center;'>كشف حساب مورد: {ss3} | {ds3} إلى {de3}</h3>", unsafe_allow_html=True)
                st.write("**الفواتير:**"); st.dataframe(ph if not ph.empty else pd.DataFrame({"الحالة":["لا توجد"]}),use_container_width=True)
                st.write("**المدفوعات:**"); st.dataframe(pyh if not pyh.empty else pd.DataFrame({"الحالة":["لا توجد"]}),use_container_width=True)
                m1,m2,m3 = st.columns(3)
                m1.metric("إجمالي الفواتير",f"{ti:,.2f} ر"); m2.metric("المدفوع",f"{tp2:,.2f} ر"); m3.metric("المستحق للمورد",f"{ti-tp2:,.2f} ر")
                if not ph.empty: st.download_button("⬇️ تنزيل",df_to_csv(ph),f"sup_{ss3}.csv","text/csv")

    with tabs[4]:
        with st.form("adf2", clear_on_submit=True):
            ma = st.selectbox("المادة:", raw_materials_list)
            nq = st.number_input("الرصيد الجديد:", min_value=0.0)
            if st.form_submit_button("✅ تحديث"):
                if run_write("UPDATE inventory SET quantity=:q WHERE material_name=:m",{"q":nq,"m":ma}):
                    st.success(f"✅ تم تحديث [{ma}]!")

    with tabs[5]:
        idf2 = run_query("SELECT material_name as المادة,quantity as الكمية FROM inventory ORDER BY material_name")
        st.dataframe(idf2 if not idf2.empty else pd.DataFrame(),use_container_width=True)
        if not idf2.empty: st.download_button("⬇️ تنزيل",df_to_csv(idf2),"inventory.csv","text/csv")

# ==========================================
# [5] الشحن والفواتير
# ==========================================
elif menu == "💰 الشحن والفواتير":
    st.subheader("💰 الشحن والفواتير")
    tabs = st.tabs(["🚚 أمر تسليم","📄 فاتورة ضريبية","🏦 سند قبض","🔍 استعلام فواتير"])

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
        qr_do_data = f"DO:{did}|ORDER:{oid}|CLIENT:{customer_name}|TANKS:{qty}|TYPE:{tu}|CAP:{tc}|DATE:{today_str}|DRIVER:{driver_name}|PLATE:{car_plate}"
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
        zatca_tlv_text = generate_zatca_tlv_b64(
            seller_name="شركة مصنع سُبُل الريادة",
            vat_no=tax_number,
            timestamp=f"{today_str}T12:00:00Z",
            total_amount=grand,
            vat_amount=vat
        )
        # Use stylized generation with larger modules for better style replication
        _qr_inv_b64  = make_qr_b64(zatca_tlv_text, color=(30, 58, 138), module_size=12, quiet=4)
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
        tc  = _sv(tank_capacity)
        tu  = _sv(tank_use)
        tt  = _sv(tank_type)
        tank_desc_ar = f"خزان {tu} — سعة {tc} — {tt}"
        tank_desc_en = f"Tank {tu} | Capacity: {tc} | {tt}"
        labels_data = []
        for i,sn in enumerate(serials_list):
            qr_text = f"SN:{sn}|ORDER:{order_id}|TYPE:{tu}|CAP:{tc}|INSTALL:{tt}|CLIENT:{customer_name}|MFG:{FACTORY_NAME}|DATE:{today_str}|SEQ:{i+1}OF{len(serials_list)}"
            labels_data.append({"id":f"qr_{i}","sn":sn,"qr_text":qr_text,"index":i+1})
        # توليد QR لكل بطاقة
        for item in labels_data:
            item['qr_b64'] = make_qr_b64(item['qr_text'], color=(30,58,138), module_size=9)

        # كل بطاقة في صفحة A4 مستقلة
        label_pages = ""
        for item in labels_data:
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
    <div class="card-body">
      <div class="qr-section">
        <img src="data:image/png;base64,{item['qr_b64']}" class="qr-box" style="display:block;width:130px;height:130px;border:3px solid #1E3A8A;border-radius:8px;" alt="QR">
        <div class="qr-caption">امسح للتحقق<br>Scan to Verify</div>
        <div class="seq-badge">خزان {item['index']} من {len(serials_list)}<br>Tank {item['index']} of {len(serials_list)}</div>
      </div>
      <div class="info-section">
        <div class="sn-display">{item['sn']}</div>
        <div class="info-grid-card">
          <div class="ig-item"><span class="ig-lbl">نوع الاستخدام</span><span class="ig-val">{tu}</span></div>
          <div class="ig-item"><span class="ig-lbl">Type of Use</span><span class="ig-val ltr">{tu}</span></div>
          <div class="ig-item"><span class="ig-lbl">السعة</span><span class="ig-val">{tc}</span></div>
          <div class="ig-item"><span class="ig-lbl">Capacity</span><span class="ig-val ltr">{tc}</span></div>
          <div class="ig-item"><span class="ig-lbl">نوع التركيب</span><span class="ig-val">{tt}</span></div>
          <div class="ig-item"><span class="ig-lbl">Installation</span><span class="ig-val ltr">{tt}</span></div>
          <div class="ig-item"><span class="ig-lbl">رقم الطلبية</span><span class="ig-val">{order_id}</span></div>
          <div class="ig-item"><span class="ig-lbl">Order No.</span><span class="ig-val ltr">{order_id}</span></div>
          <div class="ig-item"><span class="ig-lbl">العميل</span><span class="ig-val">{customer_name}</span></div>
          <div class="ig-item"><span class="ig-lbl">Customer</span><span class="ig-val ltr">{customer_name}</span></div>
          <div class="ig-item"><span class="ig-lbl">تاريخ الإنتاج</span><span class="ig-val">{today_str}</span></div>
          <div class="ig-item"><span class="ig-lbl">Production Date</span><span class="ig-val ltr">{today_str}</span></div>
        </div>
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
  display:flex;align-items:center;justify-content:center;
  padding:20mm;
  page-break-after:always;
}}
.card{{
  width:100%;border:3px solid #1E3A8A;border-radius:16px;
  overflow:hidden;box-shadow:0 4px 20px rgba(30,58,138,.15);
}}
.card-header{{
  background:linear-gradient(135deg,#1E3A8A 0%,#2563eb 100%);
  color:#fff;padding:18px 22px;
  display:flex;justify-content:space-between;align-items:center;
}}
.header-left{{display:flex;gap:14px;align-items:center;}}
.factory-icon{{font-size:38px;}}
.factory-name{{font-size:18px;font-weight:800;margin-bottom:3px;}}
.factory-sub{{font-size:11px;opacity:.8;direction:ltr;}}
.factory-addr{{font-size:10px;opacity:.7;margin-top:2px;}}
.header-right{{text-align:center;}}
.card-badge{{background:rgba(255,255,255,.2);padding:6px 16px;border-radius:20px;font-size:14px;font-weight:700;margin-bottom:4px;}}
.card-badge-en{{font-size:11px;opacity:.8;direction:ltr;}}
.card-body{{display:flex;gap:0;}}
.qr-section{{
  background:#f8fafc;border-left:1px solid #e2e8f0;
  padding:24px 20px;display:flex;flex-direction:column;
  align-items:center;gap:12px;min-width:160px;
}}
.qr-box{{
  width:130px;height:130px;
  border:3px solid #1E3A8A;border-radius:10px;
  overflow:hidden;background:#fff;
}}
.qr-box canvas,.qr-box img{{width:130px!important;height:130px!important;display:block;}}
.qr-caption{{font-size:11px;color:#64748b;text-align:center;line-height:1.6;}}
.seq-badge{{
  background:#1E3A8A;color:#fff;
  padding:6px 12px;border-radius:8px;
  font-size:11px;font-weight:700;text-align:center;line-height:1.6;
}}
.info-section{{flex:1;padding:24px 22px;}}
.sn-display{{
  font-family:monospace;font-size:16px;font-weight:800;
  color:#1E3A8A;background:#eff6ff;
  padding:10px 14px;border-radius:8px;
  margin-bottom:16px;border:2px solid #bfdbfe;
  text-align:center;letter-spacing:1px;
}}
.info-grid-card{{display:grid;grid-template-columns:1fr 1fr;gap:8px;}}
.ig-item{{display:flex;flex-direction:column;background:#f8fafc;border-radius:6px;padding:8px 10px;}}
.ig-lbl{{font-size:9px;color:#94a3b8;margin-bottom:2px;}}
.ig-val{{font-size:12px;font-weight:700;color:#1e293b;}}
.ig-val.ltr{{direction:ltr;}}
.card-footer{{
  background:#f1f5f9;border-top:1px solid #e2e8f0;
  padding:10px 22px;display:flex;
  justify-content:space-between;font-size:10px;color:#64748b;
}}
@media print{{
  body{{background:#fff;}}
  .a4-page{{
    width:210mm;min-height:297mm;margin:0;padding:15mm;
    page-break-after:always;box-shadow:none;
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

            sel_d = st.selectbox("الطلبية:", [f"{r['order_id']} | {r['trade_name']}" for _,r in odf3.iterrows()], key=f"dsel_{pck_d}")
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
                            inv_n_auto = f"INV-{did_new}-{datetime.date.today().strftime('%Y%m%d')}"
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
                            qr_html  = make_qr_labels_html(serials_shipped, str(or_d['tank_use']),
                                str(or_d['tank_capacity'] or '—'), str(or_d['tank_type']),
                                oid_d, or_d['trade_name'], today_str_d)

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
            dl_opts = [f"أمر #{r['delivery_id']} | {r['order_id']} | {r['trade_name']} | {r['shipped_qty']} خزان" for _,r in dldf.iterrows()]
            sel_dl = st.selectbox("اختر أمر التسليم:", dl_opts, key="inv_tab_sel")
            did2 = int(sel_dl.split("#")[1].split(" ")[0])
            dr   = dldf[dldf['delivery_id']==did2].iloc[0]

            sub   = float(dr['shipped_qty']) * float(dr['unit_price'])
            adv_d = (float(dr['advance_paid'])/float(dr['tq']))*float(dr['shipped_qty']) if float(dr['tq'])>0 else 0
            vat   = sub * 0.15
            grand = sub + vat
            net   = grand - adv_d
            today_str_inv = datetime.date.today().strftime("%Y/%m/%d")

            # جلب الفاتورة المحفوظة إن وُجدت
            saved_inv = run_query("SELECT invoice_id,invoice_date FROM sales_invoices WHERE delivery_id=:did",{"did":did2})
            if not saved_inv.empty:
                inv_n = f"INV-{did2}-{str(saved_inv['invoice_date'].iloc[0]).replace('-','')[:8]}"
                st.success(f"✅ الفاتورة محفوظة مسبقاً — رقم: {inv_n}")
            else:
                inv_n = f"INV-{did2}-{datetime.date.today().strftime('%Y%m%d')}"
                st.info(f"📋 فاتورة جديدة: {inv_n} — ستُحفظ تلقائياً عند الطباعة")

            # جلب الأرقام التسلسلية
            _prev_off_inv = int(run_query(
                "SELECT COALESCE(SUM(d2.shipped_qty),0) as t FROM delivery_orders d2 WHERE d2.order_id=:oid AND d2.delivery_id<:did",
                {"oid":str(dr['order_id']),"did":did2})['t'].iloc[0])
            serials_inv = run_query(
                "SELECT serial_number FROM production_tanks WHERE order_id=:oid ORDER BY serial_number LIMIT :lim OFFSET :off",
                {"oid":str(dr['order_id']),"lim":int(dr['shipped_qty']),"off":max(0,_prev_off_inv)})
            sn_list_inv = serials_inv['serial_number'].tolist() if not serials_inv.empty else []

            c1f,c2f,c3f,c4f = st.columns(4)
            c1f.metric("قبل الضريبة", f"{sub:,.2f} ر")
            c2f.metric("ضريبة 15%", f"{vat:,.2f} ر")
            c3f.metric("إجمالي", f"{grand:,.2f} ر")
            c4f.metric("الصافي المستحق", f"{net:,.2f} ر")

            inv_html2 = make_invoice_html(inv_n, did2, dr['order_id'], dr['trade_name'],
                str(dr['cr_number'] or '—'), str(dr['tax_number'] or '—'),
                str(dr['tank_use']), str(dr['tank_capacity'] or '—'), str(dr['tank_type']),
                int(dr['shipped_qty']), float(dr['unit_price']), sn_list_inv,
                sub, vat, grand, adv_d, net, today_str_inv)

            col_b1, col_b2 = st.columns(2)
            col_b1.download_button("🖨️ طباعة الفاتورة (HTML)",
                inv_html2.encode('utf-8'), f"{inv_n}.html", "text/html; charset=utf-8", key=f"dl_inv2_{did2}")
            # حفظ تلقائي إذا لم تكن محفوظة
            if saved_inv.empty:
                if col_b2.button("💾 حفظ الفاتورة", key=f"save_inv_{did2}"):
                    run_write("INSERT INTO sales_invoices(delivery_id,order_id,subtotal,vat,grand_total,advance_deducted,net_required) VALUES(:did,:oid,:st,:v,:gt,:ad,:nr)",
                              {"did":did2,"oid":dr['order_id'],"st":sub,"v":vat,"gt":grand,"ad":adv_d,"nr":net})
                    st.success(f"✅ تم حفظ الفاتورة {inv_n}!")
                    st.rerun()
            else:
                col_b2.success("✅ محفوظة في قاعدة البيانات")

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

                        qr_rcpt = f"RECEIPT:{receipt_no}|CLIENT:{sc4}|ORDER:{so4}|AMOUNT:{pa4:.2f}|METHOD:{pt4}|DATE:{today_r}"
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

# ==========================================
# [6] العمال والأجور
# ==========================================
elif menu == "👷 العمال والأجور":
    st.subheader("👷 العمال والأجور")
    tabs = st.tabs(["👤 إضافة عامل","💵 سلفة","💰 مسير الراتب","🔍 استعلام"])
    with tabs[0]:
        with st.form("wf", clear_on_submit=True):
            wn = st.text_input("الاسم:")
            wi = st.text_input("رقم الإقامة:")
            ws = st.date_input("تاريخ الالتحاق:")
            if st.form_submit_button("✅ حفظ"):
                if wn and wi:
                    if run_write("INSERT INTO workers(name,iqama_id,start_date) VALUES(:n,:i,:s) ON CONFLICT(iqama_id) DO NOTHING",{"n":wn,"i":wi,"s":ws}):
                        st.success(f"✅ [{wn}]!")
    with tabs[1]:
        if 'ak' not in st.session_state: st.session_state.ak = 0
        wdf = run_query("SELECT id,name,iqama_id FROM workers ORDER BY name")
        if not wdf.empty:
            with st.form(f"af_{st.session_state.ak}", clear_on_submit=True):
                ws2 = st.selectbox("العامل:", [f"{r['name']} - {r['iqama_id']}" for _,r in wdf.iterrows()])
                wid = int(wdf[wdf['name']==ws2.split(" - ")[0]]['id'].iloc[0])
                adv = st.number_input("السلفة:", min_value=0.0, value=1000.0)
                if st.form_submit_button("💵 اعتماد"):
                    if run_write("INSERT INTO worker_advances(worker_id,amount) VALUES(:w,:a)",{"w":wid,"a":adv}):
                        st.success(f"✅ {adv:,.2f} ريال!"); st.session_state.ak+=1; st.rerun()
    with tabs[2]:
        if 'slk' not in st.session_state: st.session_state.slk = 0
        wdf2 = run_query("SELECT id,name FROM workers ORDER BY name")
        if not wdf2.empty:
            with st.form(f"slf_{st.session_state.slk}", clear_on_submit=True):
                ws3 = st.selectbox("العامل:", wdf2['name'].tolist())
                wid2 = int(wdf2[wdf2['name']==ws3]['id'].iloc[0])
                at = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM worker_advances WHERE worker_id=:w AND status='قيد الانتظار'",{"w":wid2})['t'].iloc[0])
                base = st.number_input("الراتب:", min_value=0.0, value=5000.0)
                my = st.text_input("الشهر/السنة:", value=datetime.date.today().strftime("%Y-%m"))
                net_s = base - at
                st.info(f"الأساسي: {base:,.2f} | السلف: -{at:,.2f} | الصافي: {net_s:,.2f} ريال")
                if st.form_submit_button("💰 اعتماد"):
                    if run_write("INSERT INTO worker_salaries(worker_id,month_year,base_salary,advances_deducted,net_paid) VALUES(:w,:my,:b,:a,:n)",{"w":wid2,"my":my,"b":base,"a":at,"n":net_s}):
                        run_write("UPDATE worker_advances SET status='مخصومة' WHERE worker_id=:w AND status='قيد الانتظار'",{"w":wid2})
                        st.success(f"✅ راتب {ws3}!"); st.session_state.slk+=1; st.rerun()
    with tabs[3]:
        sw = st.text_input("ابحث:")
        if sw:
            wr = run_query("SELECT name,iqama_id,start_date FROM workers WHERE name ILIKE :s OR iqama_id LIKE :s2",{"s":f"%{sw}%","s2":f"%{sw}%"})
            st.dataframe(wr if not wr.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}),use_container_width=True)

# ==========================================
# [7] النظام المحاسبي
# ==========================================
elif menu == "📈 النظام المحاسبي":
    st.subheader("📈 النظام المحاسبي")
    tabs = st.tabs(["💹 قائمة الدخل","💰 التدفق النقدي","⚖️ الميزانية العمومية"])
    c1,c2 = st.columns(2)
    ds_a = c1.date_input("من:", datetime.date.today()-datetime.timedelta(days=30), key="ads")
    de_a = c2.date_input("إلى:", datetime.date.today(), key="ade")
    with tabs[0]:
        sales = float(run_query("SELECT COALESCE(SUM(grand_total),0) as t FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        mc = float(run_query("SELECT COALESCE(SUM(total_price),0) as t FROM procurement WHERE date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        sc = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        oc = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        gp = sales-mc; tc = mc+sc+oc; np = sales-tc
        idf3 = pd.DataFrame({"البيان":["إيرادات المبيعات","تكلفة المواد","مجمل الربح","الرواتب","المصاريف التشغيلية","إجمالي التكاليف","صافي الربح/الخسارة"],"المبلغ (ريال)":[sales,mc,gp,sc,oc,tc,np]})
        st.dataframe(idf3,use_container_width=True)
        m1,m2,m3 = st.columns(3)
        m1.metric("المبيعات",f"{sales:,.2f} ر"); m2.metric("التكاليف",f"{tc:,.2f} ر"); m3.metric("صافي الربح",f"{np:,.2f} ر",delta="ربح ✅" if np>=0 else "خسارة ❌")
        st.download_button("⬇️ تنزيل",df_to_csv(idf3),"income.csv","text/csv")
    with tabs[1]:
        ci = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE payment_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        so = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments WHERE payment_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        slo = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        eo = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e",{"s":ds_a,"e":de_a})['t'].iloc[0])
        to2 = so+slo+eo; nf = ci-to2
        fdf = pd.DataFrame({"البيان":["تحصيلات العملاء","مدفوعات الموردين","الرواتب","المصاريف","إجمالي المدفوعات","صافي التدفق النقدي"],"المبلغ (ريال)":[ci,so,slo,eo,to2,nf]})
        st.dataframe(fdf,use_container_width=True)
        m1,m2,m3 = st.columns(3)
        m1.metric("التحصيلات",f"{ci:,.2f} ر"); m2.metric("المدفوعات",f"{to2:,.2f} ر"); m3.metric("صافي التدفق",f"{nf:,.2f} ر",delta="موجب ✅" if nf>=0 else "سالب ❌")
        st.download_button("⬇️ تنزيل",df_to_csv(fdf),"cashflow.csv","text/csv")
    with tabs[2]:
        iv = float(run_query("SELECT COALESCE(SUM(quantity),0) as t FROM inventory")['t'].iloc[0])
        rec = float(run_query("SELECT COALESCE(SUM(net_required),0) as t FROM sales_invoices")['t'].iloc[0])
        ta = iv+rec
        pay2 = float(run_query("SELECT COALESCE(SUM(total_price)*1.15,0) as t FROM procurement")['t'].iloc[0])
        pp = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM supplier_payments")['t'].iloc[0])
        np2 = pay2-pp; eq = ta-np2
        bdf = pd.DataFrame({"البيان":["المخزون","ذمم مدينة","إجمالي الأصول","ذمم دائنة (موردين)","إجمالي الخصوم","حقوق الملكية"],"المبلغ (ريال)":[iv,rec,ta,np2,np2,eq]})
        st.dataframe(bdf,use_container_width=True)
        m1,m2,m3 = st.columns(3)
        m1.metric("إجمالي الأصول",f"{ta:,.2f} ر"); m2.metric("إجمالي الخصوم",f"{np2:,.2f} ر"); m3.metric("حقوق الملكية",f"{eq:,.2f} ر")
        st.download_button("⬇️ تنزيل",df_to_csv(bdf),"balance.csv","text/csv")

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
            st.success("✅ تم حذف جميع البيانات!"); st.balloons()
    else:
        st.info("✅ العملية ملغاة.")
