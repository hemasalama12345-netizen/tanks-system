import streamlit as st
import pandas as pd
import datetime
import sqlite3

# ==========================================
# 1. تأسيس وإدارة قاعدة البيانات (SQLite)
# ==========================================
def init_db():
    conn = sqlite3.connect("subul_alriyada_db.sqlite", check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول الطلبيات والمعايير القياسية (BOM)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, client_name TEXT, tank_type TEXT, qty INTEGER,
            resin_exp REAL, mat_exp REAL, roving_exp REAL, tissue_exp REAL, catalyst_exp REAL, calcium_exp REAL, silica_exp REAL
        )""")
    
    # جدول المخازن والمواد الخام
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            material_name TEXT PRIMARY KEY, quantity REAL
        )""")
    
    # جدول التصنيع الفعلي والمقارنة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS production (
            serial_number TEXT PRIMARY KEY, order_id TEXT, tank_type TEXT,
            resin_act REAL, mat_act REAL, roving_act REAL, tissue_act REAL, catalyst_act REAL, calcium_act REAL, silica_act REAL,
            prod_date TEXT, supervisor TEXT
        )""")
    
    # جدول الموردين والمشتريات
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS procurement (
            id INTEGER PRIMARY KEY AUTOINCREMENT, supplier_name TEXT, material_name TEXT, quantity REAL, unit_price REAL, total_price REAL, date TEXT
        )""")
    
    # جدول رواتب العمالة
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hr_salaries (
            emp_name TEXT PRIMARY KEY, base_salary REAL, paid REAL, remaining REAL
        )""")
    
    # جدول المصاريف التشغيلية العمومية
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, expense_type TEXT, amount REAL, date TEXT
        )""")
    
    # تغذية المخزن بالمواد الأساسية برصيد صفر إذا كانت جديدة
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        materials = [("Resin", 0.0), ("Mat 450", 0.0), ("Roving 600", 0.0), ("Tissue", 0.0), ("Catalyst", 0.0), ("Calcium Carbonate", 0.0), ("Silica", 0.0)]
        cursor.executemany("INSERT INTO inventory VALUES (?, ?)", materials)
        
    conn.commit()
    return conn

# تشغيل قاعدة البيانات
db_conn = init_db()

# ==========================================
# 2. الهوية البصرية وإعدادات النظام
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

# القائمة الجانبية والصلاحيات
st.sidebar.title("🛠️ الأقسام والعمليات")
menu = st.sidebar.radio("انتقل إلى:", [
    "📊 لوحة التحكم والميزانية", "📦 فتح طلبية جديدة (BOM)", "🏭 قائمة التصنيع والمقارنة",
    "📥 المشتريات والمخزن", "💰 الفواتير والعملاء", "👷 رواتب العمال والمصاريف"
])

# ==========================================
# 3. الأقسام التشغيلية والبرمجية
# ==========================================

# القسم 1: فتح طلبية جديدة وتحديد BOM
if menu == "📦 فتح طلبية جديدة (BOM)":
    st.subheader("📦 إدارة الطلبيات وتحديد المعايير القياسية للمنتج")
    with st.form("order_form"):
        col1, col2 = st.columns(2)
        o_id = col1.text_input("رقم / كود الطلبية الفريد (مثال: ORD-101):")
        c_name = col2.text_input("اسم العمـيل:")
        t_type = col1.selectbox("نوع الخزان ومواصفاته:", ["خزان دفن 8,000 لتر", "خزان سطحي 5,000 لتر", "مواصفة مخصصة"])
        o_qty = col2.number_input("إجمالي عدد الخزانات المطلوبة في الطلبية:", min_value=1, value=100)
        
        st.write("---")
        st.markdown("**📋 كميات المواد الخام المتوقعة والمعيارية لتصنيع (خزان واحد فقط):**")
        c3, c4, c5 = st.columns(3)
        r_ex = c3.number_input("Resin (كيلو جرام):", min_value=0.0)
        m_ex = c4.number_input("Mat 450 (كيلو جرام):", min_value=0.0)
        v_ex = c5.number_input("Roving 600 (كيلو جرام):", min_value=0.0)
        t_ex = c3.number_input("Tissue (متر مربع):", min_value=0.0)
        ca_ex = c4.number_input("Catalyst (كيلو جرام):", min_value=0.0)
        cc_ex = c5.number_input("كربونات الكالسيوم (كيلو جرام):", min_value=0.0)
        s_ex = c3.number_input("Silica (كيلو جرام):", min_value=0.0)
        
        if st.form_submit_button("حفظ الطلبية وتوليد الأرقام المسلسلة آلياً"):
            if o_id and c_name:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?,?)", 
                                   (o_id, c_name, t_type, o_qty, r_ex, m_ex, v_ex, t_ex, ca_ex, cc_ex, s_ex))
                    db_conn.commit()
                    st.success(f"✅ تم اعتماد الطلبية وتوليد أرقام مسلسلة للمنتجات من: {o_id}-001 إلى {o_id}-{o_qty:03d}")
                except sqlite3.IntegrityError:
                    st.error("🚨 رقم هذه الطلبية مسجل مسبقاً في قاعدة البيانات!")
            else:
                st.warning("الرجاء ملء حقول اسم العميل ورقم الطلبية.")

# القسم 2: قائمة التصنيع والمقارنة الفورية
elif menu == "🏭 قائمة التصنيع والمقارنة":
    st.subheader("🏭 قائمة التصنيع اليومي ومراقبة الهدر")
    
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    
    if not all_orders:
        st.info("لا توجد طلبيات مسجلة حالياً لتصنيعها. ارجع لقسم الطلبيات.")
    else:
        chosen_order = st.selectbox("اختر رقم الطلبية الجاري تصنيعها:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (chosen_order,))
        order_data = cursor.fetchone()
        
        st.info(f"العميل: {order_data[1]} | مواصفة الخزان: {order_data[2]} | الكمية المستهدفة: {order_data[3]} خزان")
        
        with st.form("prod_form"):
            col_sn1, col_sn2 = st.columns(2)
            sn_input = col_sn1.text_input("أدخل الرقم المسلسل الدقيق للخزان (مثال: ORD-101-001):")
            supervisor = col_sn2.text_input("اسم مراقب الجودة / الفني المسؤول:")
            
            st.write("---")
            st.markdown("**⚖️ الأرقام الحقيقية والفعلية المستخدمة في تصنيع هذا الخزان:**")
            c_a1, c_a2, c_a3 = st.columns(3)
            r_ac = c_a1.number_input("Resin الفعلي (كيلو جرام):")
            m_ac = c_a2.number_input("Mat 450 الفعلي (كيلو جرام):")
            v_ac = c_a3.number_input("Roving 600 الفعلي (كيلو جرام):")
            t_ac = c_a1.number_input("Tissue الفعلي (متر مربع):")
            ca_ac = c_a2.number_input("Catalyst الفعلي (كيلو جرام):")
            cc_ac = c_a3.number_input("كربونات الكالسيوم الفعلي (كيلو جرام):")
            s_ac = c_a1.number_input("Silica الفعلي (كيلو جرام):")
            
            if st.form_submit_button("اعتماد مطابقة الخزان وخصم المخازن"):
                if sn_input:
                    # خصم الكميات آلياً من جدول المخزن
                    for mat_name, act_val in [("Resin", r_ac), ("Mat 450", m_ac), ("Roving 600", v_ac), ("Tissue", t_ac), ("Catalyst", ca_ac), ("Calcium Carbonate", cc_ac), ("Silica", s_ac)]:
                        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE material_name = ?", (act_val, mat_name))
                    
                    # حفظ حركة الإنتاج الفعلي
                    cursor.execute("INSERT INTO production VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                                   (sn_input, chosen_order, order_data[2], r_ac, m_ac, v_ac, t_ac, ca_ac, cc_ac, s_ac, str(datetime.date.today()), supervisor))
                    db_conn.commit()
                    st.success(f"✅ تم حفظ بيانات الخزان {sn_input} وتحديث المستودع فورا!")
                    
                    # جدول مقارنة فوري بين المتوقع والفعلي
                    st.write("### 📊 جدول مقارنة الانحراف والخامات للخزان الحركي:")
                    labels = ["Resin", "Mat 450", "Roving 600", "Tissue", "Catalyst"]
                    exp_vals = [order_data[4], order_data[5], order_data[6], order_data[7], order_data[8]]
                    act_vals = [r_ac, m_ac, v_ac, t_ac, ca_ac]
                    diffs = [a - e for a, e in zip(act_vals, exp_vals)]
                    
                    comp_df = pd.DataFrame({"المادة الخام": labels, "الكمية المتوقعة (BOM)": exp_vals, "الكمية الفعلية المستهلكة": act_vals, "الانحراف / الهدر": diffs})
                    st.table(comp_df)

# القسم 3: المشتريات والمخزن وعمليات التوريد
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 إدارة فواتير التوريد وحسابات المخازن الحالية")
    t1, t2 = st.tabs(["🚚 تسجيل توريد خامات جديدة", "📦 جرد المخزن اللحظي"])
    
    cursor = db_conn.cursor()
    with t1:
        with st.form("proc_form"):
            supp = st.text_input("اسم مورد المواد الخام:")
            mat_select = st.selectbox("المادة الموردة:", ["Resin", "Mat 450", "Roving 600", "Tissue", "Catalyst", "Calcium Carbonate", "Silica"])
            weight = st.number_input("الكمية المستلمة (بالكيلو جرام أو المتر المربع):", min_value=0.0)
            u_p = st.number_input("سعر الوحدة / الكيلو جرام (ريال):", min_value=0.0)
            
            if st.form_submit_button("اعتماد الفاتورة وإدخال الخامات للمستودع"):
                if supp and weight > 0:
                    tot_price = weight * u_p
                    cursor.execute("INSERT INTO procurement (supplier_name, material_name, quantity, unit_price, total_price, date) VALUES (?,?,?,?,?,?)",
                                   (supp, mat_select, weight, u_p, tot_price, str(datetime.date.today())))
                    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE material_name = ?", (weight, mat_select))
                    db_conn.commit()
                    st.success(f"✅ تم إدخال الخامات بنجاح وقيد مديونية بقيمة {tot_price:,.2f} ريال للمورد {supp}")
                    
    with t2:
        cursor.execute("SELECT * FROM inventory")
        inv_data = cursor.fetchall()
        df_inv = pd.DataFrame(inv_data, columns=["المادة الخام", "الرصيد المتاح الحالي بالمستودع"])
        st.dataframe(df_inv, use_container_width=True)

# القسم 4: الفواتير ونظام حسابات العملاء
elif menu == "💰 الفواتير والعملاء":
    st.subheader("💰 نظام الفواتير المعتمد والحسابات المالية للعملاء")
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    
    if all_orders:
        selected_o = st.selectbox("اصدار فاتورة أو مراجعة حساب لطلبية رقم:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (selected_o,))
        o_data = cursor.fetchone()
        
        col_f1, col_f2 = st.columns(2)
        sell_p = col_f1.number_input("سعر بيع الخزان الواحد المتفق عليه (بدون ضريبة):", min_value=0.0, value=4000.0)
        inv_mode = col_f2.selectbox("نوع الفاتورة والائتمان:", ["نقدي فوراً", "آجل - 10 أيام", "آجل - 30 يوماً", "آجل - 60 يوماً"])
        advance_paid = col_f1.number_input("الدفعة المقدمة المستلمة من هذه الطلبية (ريال):", min_value=0.0)
        
        cursor.execute("SELECT COUNT(*) FROM production WHERE order_id=?", (selected_o,))
        done_tanks = cursor.fetchone()[0]
        
        st.write("---")
        st.subheader("📄 معاينة الفاتورة الرسمية الجاهزة للطباعة:")
        
        subtotal = done_tanks * sell_p
        vat = subtotal * 0.15
        grand_total = subtotal + vat
        remaining_balance = grand_total - advance_paid
        
        invoice_html = f"""
        <div style="border: 3px double #1E3A8A; padding: 25px; border-radius: 5px; background-color: #fff; color: #000; direction: rtl;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #1E3A8A; margin:0;">مصنع سُبُل الريادة للخزانات والمواد الصناعية</h1>
                <p style="font-size: 14px; margin:5px 0;">السجل التجاري | الرياض - المملكة العربية السعودية</p>
                <h3 style="background-color: #F1F5F9; padding: 5px; margin-top:10px;">فاتورة توريد ونقليات</h3>
            </div>
            <table style="width: 100%; margin-bottom: 20px; font-size:15px;">
                <tr><td><strong>السادة عملاء:</strong> {o_data[1]}</td><td><strong>رقم الطلبية المرجعي:</strong> {selected_o}</td></tr>
                <tr><td><strong>نوع الفاتورة:</strong> {inv_mode}</td><td><strong>التاريخ:</strong> {str(datetime.date.today())}</td></tr>
            </table>
            <table style="width: 100%; border-collapse: collapse; text-align: center; font-size:15px;" border="1">
                <tr style="background-color: #1E3A8A; color: white;"><th>وصف المنتج والبيان</th><th>الخزانات المنفذة</th><th>سعر الوحدة</th><th>الإجمالي</th></tr>
                <tr><td>{o_data[2]} بمواصفات هندسية دقيقة</td><td>{done_tanks} خزان</td><td>{sell_p:,.2f} ريال</td><td>{subtotal:,.2f} ريال</td></tr>
            </table>
            <div style="float: left; width: 40%; margin-top: 15px; font-size:14px; font-weight:bold;">
                <p>المجموع الخاضع للضريبة: {subtotal:,.2f} ريال</p>
                <p>ضريبة القيمة المضافة (15%): {vat:,.2f} ريال</p>
                <p style="border-top:1px solid #000;">الإجمالي الكلي شامل الضريبة: {grand_total:,.2f} ريال</p>
                <p style="color: green;">الدفعة المقدمة المخصومة: -{advance_paid:,.2f} ريال</p>
                <p style="color: red; border-top: 2px solid #1E3A8A; font-size:16px;">الصافي المتبقي في مديونية العميل: {remaining_balance:,.2f} ريال</p>
            </div>
            <div style="clear:both;"></div>
            <hr style="margin-top:20px;">
            <p style="text-align: center; font-size: 11px; color:#555;">صُمم خصيصاً لمصنع سبل الريادة بواسطة المهندس محمد سلامة</p>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)

# القسم 5: رواتب العمال والمصاريف التشغيلية
elif menu == "👷 رواتب العمال والمصاريف":
    st.subheader("👷 كشوفات رواتب القوى العاملة والمصاريف التشغيلية الموزعة")
    cursor = db_conn.cursor()
    
    sec1, sec2 = st.columns(2)
    with sec1:
        st.write("#### 💵 شاشة صرف الرواتب والسلف")
        e_name = st.text_input("اسم الفني / العامل بالمصنع:")
        b_sal = st.number_input("الراتب المستحق شامل الحوافز (ريال):", min_value=0.0)
        p_sal = st.number_input("المبلغ المدفوع كاش الآن (ريال):", min_value=0.0)
        
        if st.button("اعتماد مستند الصرف وطباعة السند"):
            if e_name:
                r_sal = b_sal - p_sal
                cursor.execute("INSERT OR REPLACE INTO hr_salaries VALUES (?,?,?,?)", (e_name, b_sal, p_sal, r_sal))
                db_conn.commit()
                st.success(f"تم حفظ البيانات. المتبقي في ذمة المصنع للعامل {e_name} هو {r_sal:,.2f} ريال")
                
    with sec2:
        st.write("#### ⚡ تسجيل المصاريف العمومية للطلبيات")
        cursor.execute("SELECT order_id FROM orders")
        orders_exp = [r[0] for r in cursor.fetchall()]
        
        if orders_exp:
            exp_order = st.selectbox("ربط المصروف بالطلبية رقم:", orders_exp)
            exp_type = st.selectbox("بند المصروفات:", ["فاتورة كهرباء المصنع", "فاتورة المياه", "إيجار المنشأة شهريا", "تكاليف نقليات وشحن"])
            exp_amt = st.number_input("المبلغ المدفوع للمصروف (ريال):", min_value=0.0)
            
            if st.button("قيد المصروف وحساب التكلفة"):
                cursor.execute("INSERT INTO expenses (order_id, expense_type, amount, date) VALUES (?,?,?,?)",
                               (exp_order, exp_type, exp_amt, str(datetime.date.today())))
                db_conn.commit()
                st.success(f"تم تسجيل بند {exp_type} للطلبية بنجاح.")

# القسم 6: لوحة التحكم والميزانية والتقارير العامة
elif menu == "📊 لوحة التحكم والميزانية":
    st.subheader("📈 التحليلات المالية والميزانية العمومية والربحية للمصنع")
    cursor = db_conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM production")
    total_built = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM procurement")
    raw_m_costs = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_ops_exp = cursor.fetchone()[0] or 0.0
    
    cursor.execute("SELECT SUM(paid) FROM hr_salaries")
    total_hr_paid = cursor.fetchone()[0] or 0.0
    
    # حساب إجمالي المصاريف الموزعة
    إجمالي_المصروفات_الكلية = raw_m_costs + total_ops_exp + total_hr_paid
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("إجمالي الخزانات المنتجة بالمصنع", f"{total_built} خزان")
    c_m2.metric("إجمالي التكاليف والمصاريف والرواتب تشغيلياً", f"{إجمالي_المصروفات_الكلية:,.2f} ريال")
    
    if total_built > 0:
        cost_per_tank_calc = إجمالي_المصروفات_الكلية / total_built
        c_m3.metric("التكلفة الحقيقية الموزعة للخزان الواحد حالياً", f"{cost_per_tank_calc:,.2f} ريال")
        st.info("💡 النظام يحسب التكلفة أعلاه بدقة عبر جمع (قيمة الخامات المستخدمة + الفواتير العمومية + رواتب العمال) وقسمتها على الإنتاج الفعلي الكلي.")
    else:
        c_m3.metric("التكلفة الحقيقية الموزعة للخزان الواحد حالياً", "0.00 ريال")
