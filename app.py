import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import text
import io as _io
import base64 as _b64
from PIL import Image as _Img, ImageDraw as _Draw

# اسم المصنع الثابت في النظام
FACTORY_NAME = "شركة سُبُل الريادة"

# ================================================================
# QR Code Generator — مدمج وبدون الحاجة لمكتبات خارجية معقدة
# ================================================================
_QRCODE_LIB = None
try:
    import qrcode as _qrcode_lib
    import qrcode.constants as _qrc
    _QRCODE_LIB = _qrcode_lib
except ImportError:
    pass

def make_qr_b64(text_data, color=(0,0,0), module_size=10, quiet=4):
    """توليد QR Code وتحويله إلى صيغة Base64 ليتم عرضه في Streamlit أو طباعته بـ HTML"""
    if _QRCODE_LIB is not None:
        try:
            qr = _QRCODE_LIB.QRCode(
                version=None,
                error_correction=_qrc.ERROR_CORRECT_M,
                box_size=module_size,
                border=quiet,
            )
            qr.add_data(text_data)
            qr.make(fit=True)
            r, g, b = color if isinstance(color, tuple) else (0, 0, 0)
            img = qr.make_image(fill_color=(r, g, b), back_color=(255, 255, 255))
            buf = _io.BytesIO()
            img.save(buf, format='PNG')
            return _b64.b64encode(buf.getvalue()).decode()
        except Exception:
            pass
            
    # Fallback: في حال عدم توفر المكتبة، يتم استخدام API خارجي سريع ومضمون لتوليد الرمز كصورة
    import urllib.parse
    encoded_text = urllib.parse.quote(text_data)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_text}"
    try:
        import requests
        res = requests.get(qr_url)
        if res.status_code == 200:
            return _b64.b64encode(res.content).decode()
    except Exception:
        pass
    return ""

# ================================================================
# إعدادات قاعدة البيانات والاتصال (SQLite)
# ================================================================
from sqlalchemy import create_engine
engine = create_engine("sqlite:///factory_erp.db", echo=False)

def run_query(sql, params=None):
    if params is None: params = {}
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def run_write(sql, params=None):
    if params is None: params = {}
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(sql), params)

# إنشاء الجداول الأساسية إن لم تكن موجودة
run_write("""
CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT);
""")
run_write("""
CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT);
""")
run_write("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    customer_id INTEGER, 
    tank_capacity TEXT, 
    tank_length TEXT, 
    order_date TEXT,
    status TEXT
);
""")
run_write("""
CREATE TABLE IF NOT EXISTS delivery_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    order_id INTEGER, 
    delivery_date TEXT, 
    driver_name TEXT, 
    status TEXT
);
""")
run_write("""
CREATE TABLE IF NOT EXISTS sales_invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, amount REAL, invoice_date TEXT);
""")
run_write("""
CREATE TABLE IF NOT EXISTS inventory (item_name TEXT PRIMARY KEY, quantity REAL);
""")

# إضافة عينات بيانات تجريبية إذا كانت الجداول فارغة تماماً للتجربة السهلة
if run_query("SELECT COUNT(*) FROM customers").iloc[0,0] == 0:
    run_write("INSERT INTO customers (name, phone) VALUES ('محمد الحبيب', '0500000000')")
    run_write("INSERT INTO orders (customer_id, tank_capacity, tank_length, order_date, status) VALUES (1, '8000 لتر', '3.4 متر', '2026-06-04', 'قيد التنفيذ')")
    run_write("INSERT INTO delivery_orders (order_id, delivery_date, driver_name, status) VALUES (1, '2026-06-04', 'أحمد السائق', 'جاهز للتسليم')")

def df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# ================================================================
# واجهة تطبيق Streamlit والتحكم بالقائمة
# ================================================================
st.set_page_config(page_title="نظام ERP سُبُل الريادة", layout="wide", initial_sidebar_state="expanded")
st.markdown("""<style> div.stButton > button:first-child { background-color: #007bff; color:white; } </style>""", unsafe_allow_html=True)

st.sidebar.title(f"🏭 {FACTORY_NAME}")
st.sidebar.subtitle("نظام إدارة ومتابعة خطوط الإنتاج والتسليم")

menu = st.sidebar.selectbox("📂 القائمة الرئيسية", [
    "🏠 لوحة التحكم العامة",
    "👥 إدارة العملاء والطلبات",
    "🚚 أوامر التسليم والـ QR",
    "🧾 الفواتير والمبيعات",
    "🗑️ حذف كامل للبيانات"
])

# ==========================================
# [1] لوحة التحكم العامة
# ==========================================
if menu == "🏠 لوحة التحكم العامة":
    st.title("🏠 لوحة التحكم الرئيسية")
    col1, col2, col3 = st.columns(3)
    col1.metric("عدد العملاء", len(run_query("SELECT * FROM customers")))
    col2.metric("أوامر الإنتاج والطلبات", len(run_query("SELECT * FROM orders")))
    col3.metric("أوامر التسليم الصادرة", len(run_query("SELECT * FROM delivery_orders")))

# ==========================================
# [2] إدارة العملاء والطلبات
# ==========================================
elif menu == "👥 إدارة العملاء والطلبات":
    st.title("👥 إدارة العملاء وتثبيت طلبات الخزانات")
    
    with st.expander("➕ إضافة عميل جديد"):
        c_name = st.text_input("اسم العميل")
        c_phone = st.text_input("رقم الجوال")
        if st.button("حفظ العميل"):
            if c_name:
                run_write("INSERT INTO customers (name, phone) VALUES (:name, :phone)", {"name":c_name, "phone":c_phone})
                st.success("تم حفظ العميل بنجاح!")
            else: st.error("الرجاء إدخال اسم العميل")
            
    st.subheader("📋 العملاء الحاليين")
    df_c = run_query("SELECT * FROM customers")
    st.dataframe(df_c, use_container_width=True)
    
    with st.expander("📦 إنشاء أمر إنتاج خزان جديد للعميل"):
        if not df_c.empty:
            c_options = {row['name']: row['id'] for _, row in df_c.iterrows()}
            selected_c = st.selectbox("اختر العميل", list(c_options.keys()))
            t_cap = st.text_input("سعة الخزان (مثال: 8000 لتر)")
            t_len = st.text_input("طول الخزان (مثال: 3.4 متر)")
            if st.button("إصدار أمر الإنتاج"):
                run_write("""
                    INSERT INTO orders (customer_id, tank_capacity, tank_length, order_date, status) 
                    VALUES (:cid, :cap, :len, :dt, 'قيد التنفيذ')
                """, {"cid": c_options[selected_c], "cap": t_cap, "len": t_len, "dt": str(datetime.date.today())})
                st.success("تم إصدار أمر إنتاج الخزان وجاري تحويله للتنفيذ!")
        else:
            st.warning("يجب إضافة عميل أولاً قبل إنشاء طلب.")

# ==========================================
# [3] شاشة أوامر التسليم والـ QR المتكاملة (تطبيق طلبك)
# ==========================================
elif menu == "🚚 أوامر التسليم والـ QR":
    st.title("🚚 إدارة أوامر التسليم والـ QR Code الذكي للصق على الخزانات")
    
    # 1. إنشاء أمر تسليم جديد لطلب قائم
    with st.expander("➕ إصدار إذن وأمر تسليم خزان جديد"):
        df_o = run_query("SELECT o.id, c.name, o.tank_capacity, o.tank_length FROM orders o JOIN customers c ON o.customer_id = c.id")
        if not df_o.empty:
            o_options = {f"طلب رقم {row['id']} - العميل: {row['name']} ({row['tank_capacity']})": row['id'] for _, row in df_o.iterrows()}
            selected_o = st.selectbox("اختر الطلب الجاهز للتسليم", list(o_options.keys()))
            d_driver = st.text_input("اسم السائق / شركة الشحن")
            d_date = st.date_input("تاريخ التسليم المتوقع", datetime.date.today())
            
            if st.button("تثبيت أمر التسليم"):
                run_write("""
                    INSERT INTO delivery_orders (order_id, delivery_date, driver_name, status) 
                    VALUES (:oid, :ddate, :driver, 'جاهز للتسليم')
                """, {"oid": o_options[selected_o], "ddate": str(d_date), "driver": d_driver})
                st.success("تم تسجيل أمر التسليم وتوليد معرّف الـ QR بنجاح!")
        else:
            st.warning("لا توجد طلبات إنتاج حالية لإصدار أذن تسليم لها.")

    # 2. استعراض أوامر التسليم الحالية مع الـ QR للطباعة والعرض
    st.subheader("📋 أذونات وأوامر التسليم الصادرة")
    df_deliv = run_query("""
        SELECT 
            do.id AS 'رقم أمر التسليم', 
            do.order_id AS 'رقم الطلب', 
            c.name AS 'اسم العميل', 
            o.tank_capacity AS 'سعة الخزان', 
            o.tank_length AS 'الطول', 
            do.driver_name AS 'السائق', 
            do.delivery_date AS 'تاريخ التسليم', 
            do.status AS 'الحالة'
        FROM delivery_orders do
        JOIN orders o ON do.order_id = o.id
        JOIN customers c ON o.customer_id = c.id
    """)
    
    if not df_deliv.empty:
        st.dataframe(df_deliv, use_container_width=True)
        
        # اختيار أمر تسليم معين لاستعراض الـ QR وطباعة المستند بالكامل
        st.markdown("---")
        st.subheader("🖨️ طباعة مستند التسليم مع الـ QR Code الذكي")
        
        deliv_ids = df_deliv['رقم أمر التسليم'].tolist()
        selected_deliv_id = st.selectbox("اختر رقم أمر التسليم لعرض بطاقة اللصق والـ QR الخاصة به:", deliv_ids)
        
        # جلب بيانات السجل المحدد بدقة
        target_row = df_deliv[df_deliv['رقم أمر التسليم'] == selected_deliv_id].iloc[0]
        
        # صياغة بيانات الخزان المضمنة داخل كود الـ QR ليكون مقروءاً من أي جوال بدقة
        qr_text_content = (
            f"المصنع: {FACTORY_NAME}\n"
            f"رقم إذن التسليم: {target_row['رقم أمر التسليم']}\n"
            f"العميل: {target_row['اسم العميل']}\n"
            f"سعة الخزان: {target_row['سعة الخزان']}\n"
            f"طول الخزان: {target_row['الطول']}\n"
            f"تاريخ الخروج: {target_row['تاريخ التسليم']}\n"
            f"الحالة: تم الفحص والتسليم بنجاح"
        )
        
        # توليد كود الـ QR بصيغة Base64
        qr_img_b64 = make_qr_b64(qr_text_content)
        
        col_view, col_print = st.columns([1, 2])
        
        with col_view:
            st.markdown("### 🔍 معاينة الـ QR Code")
            if qr_img_b64:
                st.image(f"data:image/png;base64,{qr_img_b64}", width=200, caption="رمز الخزان المخصص للصق")
            else:
                st.error("فشل في توليد الرمز التعبيري")
                
        with col_print:
            st.markdown("### 📄 إذن التسليم الرسمي الجاهز للطباعة")
            
            # قالب HTML احترافي لطباعة إذن التسليم متضمن الـ QR كجزء أساسي من الورقة الرسمية للمصنع
            html_invoice_template = f"""
            <div style="direction: rtl; text-align: right; border: 2px solid #333; padding: 20px; font-family: 'Arial', sans-serif; background-color: #fff; color: #000; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 15px;">
                    <div>
                        <h2 style="margin: 0; color: #004085;">{FACTORY_NAME}</h2>
                        <p style="margin: 4px 0; font-size: 13px; color: #555;">إذن تسليم منتج نهائي مخصص للصق</p>
                    </div>
                    <div style="text-align: left;">
                        <h4 style="margin: 0;">رقم المستند: {target_row['رقم أمر التسليم']}</h4>
                        <p style="margin: 4px 0; font-size: 13px;">التاريخ: {target_row['تاريخ التسليم']}</p>
                    </div>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 15px;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">البيان</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">التفاصيل ومواصفات الخزان</th>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><b>اسم العميل المكرم</b></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{target_row['اسم العميل']}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><b>سعة الخزان المطلوبة</b></td>
                        <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; color: #d9534f;">{target_row['سعة الخزان']}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><b>الأبعاد (الطول)</b></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{target_row['الطول']}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><b>المسؤول عن النقل</b></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{target_row['السائق']}</td>
                    </tr>
                </table>
                
                <div style="display: flex; justify-content: space-between; align-items: center; background-color: #f9f9f9; padding: 15px; border: 1px dashed #999; border-radius: 6px;">
                    <div>
                        <p style="margin: 0 0 8px 0; font-size: 13px;">💡 <b>ملاحظة فنية للموقع والأمن:</b></p>
                        <p style="margin: 0; font-size: 12px; color: #666;">يرجى مسح الـ QR المقابل عبر الكاميرا للتأكد من مطابقة الخزان الخارج من بوابة المصنع مع بيانات العميل في النظام لمنع أي أخطاء تحميل.</p>
                    </div>
                    <div style="text-align: center; margin-right: 15px;">
                        <img src="data:image/png;base64,{qr_img_b64}" width="140" height="140" style="border: 1px solid #ccc; padding: 4px; background: #fff;" />
                        <div style="font-size: 10px; font-weight: bold; color: #333; margin-top: 5px;">مسح الرمز (QR Code)</div>
                    </div>
                </div>
                
                <div style="margin-top: 20px; display: flex; justify-content: space-between; font-size: 13px;">
                    <div><b>توقيع مستودع الإنتاج:</b> ............................</div>
                    <div><b>توقيع أمن البوابة الخارجية:</b> ............................</div>
                    <div><b>توقيع السائق بالاستلام:</b> ............................</div>
                </div>
            </div>
            """
            st.components.v1.html(html_invoice_template, height=480, scroller=True)
            st.info("💡 يمكنك الضغط بزر الفأرة الأيمن داخل المربع أعلاه واختيار (Print) لطباعة بطاقة الخزان فوراً.")
    else:
        st.info("لا توجد أوامر تسليم مسجلة حالياً لعرض بطاقات الـ QR الخاصة بها.")

# ==========================================
# [4] الفواتير والمبيعات
# ==========================================
elif menu == "🧾 الفواتير والمبيعات":
    st.title("🧾 إدارة الفواتير والمبيعات المباشرة")
    with st.expander("➕ إصدار فاتورة جديدة"):
        df_del = run_query("SELECT id FROM delivery_orders")
        if not df_del.empty:
            del_id = st.selectbox("اختر رقم إذن التسليم المالي", df_del['id'].tolist())
            inv_amount = st.number_input("إجمالي قيمة الفاتورة (ريال)", min_value=0.0)
            if st.button("تثبيت وحفظ الفاتورة"):
                run_write("INSERT INTO sales_invoices (order_id, amount, invoice_date) VALUES (:oid, :amt, :dt)",
                          {"oid": del_id, "amt": inv_amount, "dt": str(datetime.date.today())})
                st.success("تم إصدار الفاتورة وحفظها في الحسابات المبيعات!")
        else:
            st.warning("يجب إنشاء أمر تسليم أولاً لتتمكن من إدخال فاتورته المادية.")

    st.subheader("📋 قائمة الفواتير الصادرة")
    st.dataframe(run_query("SELECT * FROM sales_invoices"), use_container_width=True)

# ==========================================
# [5] حذف كامل للبيانات (كما ورد بملفك)
# ==========================================
elif menu == "🗑️ حذف كامل للبيانات":
    st.subheader("🗑️ حذف كامل للبيانات وتصفير النظام")
    st.error("⚠️ تحذير شديد: هذه العملية تحذف جميع سجلات الإنتاج والعملاء والـ QR نهائياً!")
    cf = st.radio("هل أنت متأكد تماماً من الرغبة في التصفير الشامل؟", ["لا، إلغاء التصفير", "نعم، أريد الحذف الشامل وقاعدة بيانات جديدة"])
    
    if cf == "نعم، أريد الحذف الشامل وقاعدة بيانات جديدة":
        st.warning("⚠️ هذا هو التحذير الأخير قبل محو السجلات!")
        if st.button("🗑️ تأكيد الحذف الكامل الفوري — لا يمكن التراجع"):
            tables = ["sales_invoices", "delivery_orders", "orders", "customers", "suppliers", "inventory"]
            for t in tables:
                try:
                    run_write(f"DELETE FROM {t}")
                except Exception:
                    pass
            st.success("تم مسح قاعدة البيانات بنجاح وتجهيز النظام لبيانات جديدة!")
            st.balloons()
