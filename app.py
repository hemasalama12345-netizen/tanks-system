
import streamlit as st
import pandas as pd
import datetime
import sqlite3

# ==========================================
# 1. تأسيس وإدارة قاعدة البيانات (نسخة نظيفة وصفرية)
# ==========================================
def init_db():
    conn = sqlite3.connect("subul_alriyada_final.sqlite", check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, client_name TEXT, tank_type TEXT, qty INTEGER, advance_paid REAL,
            resin_exp REAL, mat_exp REAL, roving_exp REAL, tissue_exp REAL, catalyst_exp REAL, calcium_exp REAL, silica_exp REAL
        )""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            material_name TEXT PRIMARY KEY, quantity REAL
        )""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS production (
            serial_number TEXT PRIMARY KEY, order_id TEXT, tank_type TEXT,
            resin_act REAL, mat_act REAL, roving_act REAL, tissue_act REAL, catalyst_act REAL, calcium_act REAL, silica_act REAL,
            prod_date TEXT, supervisor TEXT
        )""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS procurement (
            id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT, material_name TEXT, quantity REAL, unit_price REAL, total_price REAL, date TEXT
        )""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr_salaries (
            emp_name TEXT PRIMARY KEY, base_salary REAL, paid REAL, remaining REAL
        )""")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, expense_type TEXT, amount REAL, date TEXT
        )""")
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        materials = [
            ("راتنج (Resin)", 0.0), 
            ("ألياف (Mat 450)", 0.0), 
            ("روفرز (Roving 600)", 0.0), 
            ("تيسو (Tissue)", 0.0), 
            ("مصلد (Catalyst)", 0.0), 
            ("كربونات الكالسيوم", 0.0), 
            ("سيليكا (Silica)", 0.0)
        ]
        cursor.executemany("INSERT INTO inventory VALUES (?, ?)", materials)
        
    conn.commit()
    return conn

db_conn = init_db()

# ==========================================
# 2. الهوية البصرية وإعدادات التنسيق
# ==========================================
st.set_page_config(page_title="مصنع سُبُل الريادة - ERP", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .stApp {
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
    }
    .main-header { font-size: 32px; color: #1E3A8A; font-weight: bold; border-bottom: 3px solid #FBBF24; padding-bottom: 5px; }
    .designer-tag { font-size: 14px; color: #64748B; background: #F1F5F9; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom:20px;">'
            f'<div class="main-header">🏭 نظام إدارة مصنع سُبُل الريادة الاحترافي</div>'
            f'<div class="designer-tag">تصميم المهندس محمد سلامة</div>'
            f'</div>', unsafe_allow_html=True)

st.sidebar.title("🛠️ الأقسام والعمليات")
menu = st.sidebar.radio("انتقل إلى:", [
    "📊 لوحة التحكم والميزانية", "📦 فتح طلبية جديدة (BOM)", "🏭 قائمة التصنيع والمقارنة",
    "📥 المشتريات والمخزن", "💰 الفواتير والعملاء", "👷 رواتب العمال والمصاريف"
])

raw_materials_list = ["راتنج (Resin)", "ألياف (Mat 450)", "روفرز (Roving 600)", "تيسو (Tissue)", "مصلد (Catalyst)", "كربونات الكالسيوم", "سيليكا (Silica)"]

# ==========================================
# 3. الأقسام والتبويبات التشغيلية
# ==========================================

if menu == "📦 فتح طلبية جديدة (BOM)":
    st.subheader("📦 إدارة الطلبيات وتحديد المعايير القياسية للمنتج")
    with st.form("order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        o_id = col1.text_input("رقم / كود الطلبية الفريد (مثال: ORD-101):")
        c_name = col2.text_input("اسم العمـيل:")
        t_type = col1.selectbox("نوع الخزان ومواصفاته:", ["خزان دفن 8,000 لتر", "خزان سطحي 5,000 لتر", "مواصفة مخصصة"])
        o_qty = col2.number_input("إجمالي عدد الخزانات المطلوبة في الطلبية:", min_value=1, value=1)
        advance_p = col1.number_input("الدفعة المقدمة المستلمة لهذه الطلبية (ريال):", min_value=0.0, value=0.0)
        
        st.write("---")
        st.markdown("**📋 كميات المواد الخام المتوقعة والمعيارية لتصنيع (خزان واحد فقط):**")
        c3, c4, c5 = st.columns(3)
        r_ex = c3.number_input("راتنج - Resin (كيلو جرام):", min_value=0.0)
        m_ex = c4.number_input("ألياف - Mat 450 (كيلو جرام):", min_value=0.0)
        v_ex = c5.number_input("روفرز - Roving 600 (كيلو جرام):", min_value=0.0)
        t_ex = c3.number_input("تيسو - Tissue (متر مربع):", min_value=0.0)
        ca_ex = c4.number_input("مصلد - Catalyst (كيلو جرام):", min_value=0.0)
        cc_ex = c5.number_input("كربونات الكالسيوم (كيلو جرام):", min_value=0.0)
        s_ex = c3.number_input("سيليكا - Silica (كيلو جرام):", min_value=0.0)
        
        if st.form_submit_button("حفظ الطلبية وتوليد الأرقام المسلسلة آلياً"):
            if o_id and c_name:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                                   (o_id, c_name, t_type, o_qty, advance_p, r_ex, m_ex, v_ex, t_ex, ca_ex, cc_ex, s_ex))
                    db_conn.commit()
                    st.success(f"✅ تم اعتماد الطلبية {o_id} بنجاح، وتفريغ النموذج.")
                except sqlite3.IntegrityError:
                    st.error("🚨 رقم هذه الطلبية مسجل مسبقاً!")

elif menu == "🏭 قائمة التصنيع والمقارنة":
    st.subheader("🏭 قائمة التصنيع اليومي ومراقبة الهدر")
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    
    if not all_orders:
        st.info("لا توجد طلبيات مسجلة حالياً.")
    else:
        chosen_order = st.selectbox("اختر رقم الطلبية الجاري تصنيعها:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (chosen_order,))
        order_data = cursor.fetchone()
        
        with st.form("prod_form", clear_on_submit=True):
            col_sn1, col_sn2 = st.columns(2)
            sn_input = col_sn1.text_input("أدخل الرقم المسلسل الدقيق للخزان:")
            supervisor = col_sn2.text_input("اسم مراقب الجودة / الفني المسؤول:")
            
            c_a1, c_a2, c_a3 = st.columns(3)
            r_ac = c_a1.number_input("راتنج الفعلي (كيلو جرام):")
            m_ac = c_a2.number_input("ألياف الفعلي (كيلو جرام):")
            v_ac = c_a3.number_input("روفرز الفعلي (كيلو جرام):")
            t_ac = c_a1.number_input("تيسو الفعلي (متر مربع):")
            ca_ac = c_a2.number_input("مصلد الفعلي (كيلو جرام):")
            cc_ac = c_a3.number_input("كربونات الكالسيوم الفعلي (كيلو جرام):")
            s_ac = c_a1.number_input("سيليكا الفعلي (كيلو جرام):")
            
            if st.form_submit_button("اعتماد مطابقة الخزان وخصم المخازن"):
                if sn_input:
                    cursor.execute("INSERT INTO production VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (sn_input, chosen_order, order_data[2], r_ac, m_ac, v_ac, t_ac, ca_ac, cc_ac, s_ac, str(datetime.date.today()), supervisor))
                    
                    materials_map = [
                        ("راتنج (Resin)", r_ac), ("ألياف (Mat 450)", m_ac), ("روفرز (Roving 600)", v_ac), 
                        ("تيسو (Tissue)", t_ac), ("مصلد (Catalyst)", ca_ac), ("كربونات الكالسيوم", cc_ac), ("سيليكا (Silica)", s_ac)
                    ]
                    for m_n, val in materials_map:
                        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE material_name = ?", (val, m_n))
                    db_conn.commit()
                    st.success(f"✅ تم تسجيل حركة إنتاج الخزان {sn_input} وتصفير الحقول.")

elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 المشتريات وجرد وتصحيح أرصدة المستودع")
    t1, t2, t3 = st.tabs(["🚚 توريد خامات جديدة", "🔧 تعديل الرصيد الحالي (تصحيح أخطاء)", "📦 جرد المخزن اللحظي"])
    cursor = db_conn.cursor()
    
    with t1:
        with st.form("proc_form", clear_on_submit=True):
            supp = st.text_input("اسم المورد:")
            mat_select = st.selectbox("المادة الموردة:", raw_materials_list)
            weight = st.number_input("الكمية المستلمة المضافة:", min_value=0.0)
            u_p = st.number_input("سعر الوحدة الحالي (ريال):", min_value=0.0)
            if st.form_submit_button("اعتماد دخول الشحنة للمستودع"):
                if supp and weight > 0:
                    cursor.execute("INSERT INTO procurement (supplier_name, material_name, quantity, unit_price, total_price, date) VALUES (?,?,?,?,?,?)",
                                   (supp, mat_select, weight, u_p, weight*u_p, str(datetime.date.today())))
                    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE material_name = ?", (weight, mat_select))
                    db_conn.commit()
                    st.success("👍 تم التوريد بنجاح، وأصبحت الخانات فارغة بالكامل.")
                    
    with t2:
        st.write("#### ⚠️ شاشة التعديل المباشر للأرصدة (في حال الإدخال الخاطئ)")
        with st.form("adjust_form", clear_on_submit=True):
            adj_mat = st.selectbox("اختر المادة المراد ضبط رصيدها:", raw_materials_list)
            new_qty = st.number_input("أدخل الرصيد الفعلي الموجود بالمخزن الآن (سيستبدل القديم بالكامل):", min_value=0.0)
            if st.form_submit_button("تحديث وتعديل رصيد المخزن فوراً"):
                cursor.execute("UPDATE inventory SET quantity = ? WHERE material_name = ?", (new_qty, adj_mat))
                db_conn.commit()
                st.success(f"✅ تم تصحيح رصيد مادة [{adj_mat}] ليصبح الدقيق هو: {new_qty} كجم/م2.")
                
    with t3:
        cursor.execute("SELECT * FROM inventory")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["المادة الخام", "الرصيد المتاح الحالي بالمستودع"]), use_container_width=True)

elif menu == "💰 الفواتير والعملاء":
    st.subheader("💰 نظام الفواتير المعتمد للعملاء")
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    if all_orders:
        selected_o = st.selectbox("اختر رقم الطلبية المرجعية للفاتورة:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (selected_o,))
        o_data = cursor.fetchone()
        sell_p = st.number_input("سعر بيع الخزان الواحد المتفق عليه (بدون ضريبة):", min_value=0.0, value=4000.0)
        inv_mode = st.selectbox("نوع الائتمان بالفاتورة الحالية:", ["نقدي فوراً", "آجل - 30 يوماً", "آجل - 60 يوماً"])
        
        cursor.execute("SELECT COUNT(*), group_concat(serial_number) FROM production WHERE order_id=?", (selected_o,))
        prod_res = cursor.fetchone()
        done_tanks = prod_res[0] or 0
        serials_list = prod_res[1] or "لا يوجد"
        
        subtotal = done_tanks * sell_p
        vat = subtotal * 0.15
        grand_total = subtotal + vat
        remaining_balance = grand_total - o_data[4]
        
        invoice_html = f"""
        <div style="border: 3px double #1E3A8A; padding: 20px; border-radius: 5px; background-color: #fff; color: #000; direction: rtl;">
            <div style="text-align: center;">
                <h2 style="color: #1E3A8A; margin:0;">مصنع سُبُل الريادة للخزانات والمواد الصناعية</h2>
                <h4 style="background-color: #F1F5F9; padding: 5px; margin-top:5px;">فاتورة مبيعات ضريبية هندسية</h4>
            </div>
            <p><strong>السادة عملاء:</strong> {o_data[1]} | <strong>رقم الطلبية:</strong> {selected_o}</p>
            <p><strong>نوع الفاتورة والائتمان:</strong> {inv_mode} | <strong>الأرقام المسلسلة المشمولة:</strong> {serials_list}</p>
            <table style="width: 100%; border-collapse: collapse; text-align: center;" border="1">
                <tr style="background-color: #1E3A8A; color: white;"><th>البيان ومواصفات التوريد</th><th>الكمية المنفذة</th><th>سعر الوحدة</th><th>الإجمالي قبل الضريبة</th></tr>
                <tr><td>{o_data[2]}</td><td>{done_tanks} خزان</td><td>{sell_p:,.2f} ريال</td><td>{subtotal:,.2f} ريال</td></tr>
            </table>
            <div style="float: left; width: 45%; margin-top: 15px; font-weight:bold;">
                <p>المجموع الخاضع للضريبة: {subtotal:,.2f} ريال</p>
                <p>ضريبة القيمة المضافة (15%): {vat:,.2f} ريال</p>
                <p style="color: green;">الدفعة المقدمة المخصومة: -{o_data[4]:,.2f} ريال</p>
                <p style="color: red; border-top: 2px solid #1E3A8A; font-size:16px;">الصافي المستحق بمديونية العميل: {remaining_balance:,.2f} ريال</p>
            </div>
            <div style="clear:both;"></div>
            <p style="text-align: center; font-size: 11px; color:#555; margin-top:20px;">صُمم خصيصاً لمصنع سبل الريادة بواسطة المهندس محمد سلامة</p>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)

elif menu == "👷 رواتب العمال والمصاريف":
    st.subheader("👷 رواتب القوى العاملة والمصاريف العمومية")
    cursor = db_conn.cursor()
    sec1, sec2 = st.columns(2)
    with sec1:
        st.write("#### 💵 كشف صرف الرواتب والسلف")
        with st.form("salary_form", clear_on_submit=True):
            e_name = st.text_input("اسم العامل الفني:")
            b_sal = st.number_input("الراتب الإجمالي المستحق بالشهر (ريال):")
            p_sal = st.number_input("المبلغ المدفوع كاش الآن:")
            if st.form_submit_button("اعتماد مستند صرف راتب"):
                if e_name:
                    cursor.execute("INSERT OR REPLACE INTO hr_salaries VALUES (?,?,?,?)", (e_name, b_sal, p_sal, b_sal-p_sal))
                    db_conn.commit()
                    st.success(f"تم التسجيل بنظام الأجور والرواتب والمتبقي بذمة المصنع: {b_sal-p_sal:,.2f} ريال")
    with sec2:
        st.write("#### ⚡ المصاريف التشغيلية")
        cursor.execute("SELECT order_id FROM orders")
        orders_exp = [r[0] for r in cursor.fetchall()]
        if orders_exp:
            with st.form("exp_form", clear_on_submit=True):
                exp_order = st.selectbox("ربط التكلفة بالطلبية رقم:", orders_exp)
                exp_type = st.selectbox("بند المصروف المصنعي الإداري:", ["كهرباء المصنع", "مياه", "إيجار المنشأة", "شحن ونقليات"])
                exp_amt = st.number_input("قيمة المدفوعات النقدية (ريال):")
                if st.form_submit_button("قيد المصروف الإداري للطلبية"):
                    cursor.execute("INSERT INTO expenses (order_id, expense_type, amount, date) VALUES (?,?,?,?)", (exp_order, exp_type, exp_amt, str(datetime.date.today())))
                    db_conn.commit()
                    st.success("تم قيد البند المالي بالدفاتر بنجاح.")

elif menu == "📊 لوحة التحكم والميزانية":
    st.subheader("📈 الميزانية والتقارير الشهرية للمصنع")
    cursor = db_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM production")
    total_built = cursor.fetchone()[0]
    cursor.execute("SELECT SUM(total_price) FROM procurement")
    raw_costs = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_ops = cursor.fetchone()[0] or 0.0
    cursor.execute("SELECT SUM(paid) FROM hr_salaries")
    total_hr = cursor.fetchone()[0] or 0.0
    
    total_costs_calc = raw_costs + total_ops + total_hr
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("إجمالي الخزانات المنتجة حياً", f"{total_built} خزان")
    c_m2.metric("إجمالي التكاليف والمصاريف والرواتب الكلية", f"{total_costs_calc:,.2f} ريال")
    if total_built > 0:
        c_m3.metric("التكلفة الحقيقية الموزعة للخزان الواحد حالياً", f"{(total_costs_calc/total_built):,.2f} ريال")
    else:
        c_m3.metric("التكلفة الحقيقية الموزعة للخزان الواحد حالياً", "0.00 ريال")
