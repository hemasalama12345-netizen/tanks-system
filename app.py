import streamlit as st
import pandas as pd
import datetime
import sqlite3

# ==========================================
# 1. تأسيس وإدارة قاعدة البيانات (النسخة الرابعة المتطورة)
# ==========================================
def init_db():
    conn = sqlite3.connect("subul_alriyada_v4.sqlite", check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول الطلبيات المحدث بالمواصفات الجديدة والأسعار
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY, client_name TEXT, tank_use TEXT, tank_capacity TEXT, tank_type TEXT, 
            qty INTEGER, unit_price REAL, advance_paid REAL,
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
            serial_number TEXT PRIMARY KEY, order_id TEXT, tank_desc TEXT,
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
    
    cursor.execute("SELECT COUNT(*) FROM inventory")
    if cursor.fetchone()[0] == 0:
        materials = [
            ("راتنج (Resin)", 0.0), ("ألياف (Mat 450)", 0.0), ("روفرز (Roving 600)", 0.0), 
            ("تيسو (Tissue)", 0.0), ("مصلد (Catalyst)", 0.0), ("كربونات الكالسيوم", 0.0), ("سيليكا (Silica)", 0.0)
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
    "📊 لوحة التحكم والميزانية", "📦 فتح وإدارة الطلبيات", "🏭 قائمة التصنيع والمقارنة",
    "📥 المشتريات والمخزن", "💰 الفواتير والعملاء", "👷 رواتب العمال والمصاريف"
])

raw_materials_list = ["راتنج (Resin)", "ألياف (Mat 450)", "روفرز (Roving 600)", "تيسو (Tissue)", "مصلد (Catalyst)", "كربونات الكالسيوم", "سيليكا (Silica)"]

# ==========================================
# 3. قسم إدارة الطلبيات المطور بالكامل
# ==========================================
if menu == "📦 فتح وإدارة الطلبيات":
    st.subheader("📦 منظومة إدارة وحسابات الطلبيات المركزية")
    tab_new, tab_edit, tab_view = st.tabs(["➕ فتح طلبية جديدة", "📝 تعديل طلبية قائمة", "📋 الطلبيات قيد التنفيذ"])
    
    with tab_new:
        # استخدام المدخلات الحية خارج الفورم ليعمل الحساب التلقائي فوراً وبشكل مباشر
        c1, c2 = st.columns(2)
        new_o_id = c1.text_input("رقم / كود الطلبية الفريد (مثال: ORD-101):", key="new_o_id")
        new_c_name = c2.text_input("اسم العمـيل:", key="new_c_name")
        
        c3, c4, c5 = st.columns(3)
        new_t_use = c3.selectbox("استخدام الخزان:", ["ماء", "صرف", "ديزل", "حريق"], key="new_t_use")
        new_t_cap = c4.text_input("سعة الخزان (مثال: 8000 لتر أو 120 م3):", key="new_t_cap")
        new_t_type = c5.selectbox("نوع التركيب والوضع:", ["دفّان", "فوق الأرض"], key="new_t_type")
        
        c6, c7 = st.columns(2)
        new_qty = c6.number_input("كمية الخزانات المطلوبة بالطلبية:", min_value=1, value=1, key="new_qty")
        new_price = c7.number_input("سعر الخزان الواحد (ريال):", min_value=0.0, value=0.0, key="new_price")
        
        c8, c9 = st.columns(2)
        adv_mode = c8.selectbox("طريقة إدخال الدفعة المقدمة:", ["رقم محدد بالريال", "نسبة مئوية من الإجمالي (%)"])
        adv_val_input = c9.number_input("قيمة الدفعة المقدمة المدخلة:", min_value=0.0, value=0.0)
        
        # الحسابات المالية اللحظية والمباشرة أمام المهندس والعميل
        total_order_value = new_qty * new_price
        if adv_mode == "نسبة مئوية من الإجمالي (%)":
            calculated_advance = (total_order_value * adv_val_input) / 100
        else:
            calculated_advance = adv_val_input
        remaining_balance = total_order_value - calculated_advance
        
        st.markdown("---")
        st.markdown("### 📊 خلاصة الحسبة المادية اللحظية للطلبية:")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("إجمالي قيمة الطلبية (بدون ضريبة)", f"{total_order_value:,.2f} ريال")
        col_m2.metric("الدفعة المقدمة الصافية", f"{calculated_advance:,.2f} ريال")
        col_m3.metric("المبلغ المتبقي على الطلبية", f"{remaining_balance:,.2f} ريال", delta=f"-{calculated_advance:,.2f}", delta_color="inverse")
        
        st.markdown("---")
        st.markdown("**📋 كميات المواد الخام المتوقعة والمعيارية لتصنيع (خزان واحد فقط) من هذه المواصفة:**")
        cx1, cx2, cx3 = st.columns(3)
        r_ex = cx1.number_input("راتنج - Resin (كجم):", min_value=0.0, key="r_ex")
        m_ex = cx2.number_input("ألياف - Mat 450 (كجم):", min_value=0.0, key="m_ex")
        v_ex = cx3.number_input("روفرز - Roving 600 (كجم):", min_value=0.0, key="v_ex")
        t_ex = cx1.number_input("تيسو - Tissue (م2):", min_value=0.0, key="t_ex")
        ca_ex = cx2.number_input("مصلد - Catalyst (كجم):", min_value=0.0, key="ca_ex")
        cc_ex = cx3.number_input("كربونات الكالسيوم (كجم):", min_value=0.0, key="cc_ex")
        s_ex = cx1.number_input("سيليكا - Silica (كجم):", min_value=0.0, key="s_ex")
        
        if st.button("🚀 اعتماد وحفظ الطلبية وتوليد السيريال آلياً"):
            if new_o_id and new_c_name:
                try:
                    cursor = db_conn.cursor()
                    cursor.execute("""
                        INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (new_o_id, new_c_name, new_t_use, new_t_cap, new_t_type, new_qty, new_price, calculated_advance,
                         r_ex, m_ex, v_ex, t_ex, ca_ex, cc_ex, s_ex))
                    db_conn.commit()
                    st.success(f"✅ تم بنجاح حفظ الطلبية {new_o_id} وتفريغ الاستمارة بالكامل لعملية جديدة!")
                    # تصفير الخانات برمجياً عبر إعادة تهيئة الصفحة لنظافة تامة
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("🚨 كود هذه الطلبية مسجل مسبقاً بقاعدة البيانات، يرجى كتابة كود فريد.")
            else:
                st.warning("الرجاء كتابة كود الطلبية واسم العميل أولاً لحمايتك.")

    with tab_edit:
        st.write("#### 📝 تعديل بيانات ومواصفات طلبية قائمة")
        cursor = db_conn.cursor()
        cursor.execute("SELECT order_id FROM orders")
        editable_orders = [r[0] for r in cursor.fetchall()]
        
        if not editable_orders:
            st.info("لا توجد طلبيات مسجلة لتعديلها حالياً.")
        else:
            selected_edit = st.selectbox("اختر كود الطلبية المراد تعديل بياناتها بالكامل:", editable_orders)
            cursor.execute("SELECT * FROM orders WHERE order_id=?", (selected_edit,))
            old_d = cursor.fetchone()
            
            # عرض البيانات الحالية داخل خانات قابلة للتعديل مباشرة
            ce1, ce2 = st.columns(2)
            edit_c_name = ce1.text_input("تعديل اسم العميل:", value=old_d[1])
            edit_t_use = ce2.selectbox("تعديل استخدام الخزان:", ["ماء", "صرف", "ديزل", "حريق"], index=["ماء", "صرف", "ديزل", "حريق"].index(old_d[2]))
            
            ce3, ce4, ce5 = st.columns(3)
            edit_t_cap = ce3.text_input("تعديل سعة الخزان:", value=old_d[3])
            edit_t_type = ce4.selectbox("تعديل نوع الخزان:", ["دفّان", "فوق الأرض"], index=["دفّان", "فوق الأرض"].index(old_d[4]))
            edit_qty = ce5.number_input("تعديل كمية الخزانات بالطلب:", min_value=1, value=int(old_d[5]))
            
            ce6, ce7 = st.columns(2)
            edit_price = ce6.number_input("تعديل سعر الخزان الواحد:", min_value=0.0, value=float(old_d[6]))
            edit_advance = ce7.number_input("تعديل الدفعة المقدمة المستلمة (ريال):", min_value=0.0, value=float(old_d[7]))
            
            st.write("🔧 **تعديل كميات الخامات المعيارية (BOM) للخزان الواحد:**")
            cex1, cex2, cex3 = st.columns(3)
            edit_r = cex1.number_input("راتنج المعدل:", value=old_d[8])
            edit_m = cex2.number_input("ألياف المعدل:", value=old_d[9])
            edit_v = cex3.number_input("روفرز المعدل:", value=old_d[10])
            
            if st.button("💾 حفظ وتحديث التعديلات الجديدة"):
                cursor.execute("""
                    UPDATE orders SET client_name=?, tank_use=?, tank_capacity=?, tank_type=?, qty=?, unit_price=?, advance_paid=?,
                    resin_exp=?, mat_exp=?, roving_exp=? WHERE order_id=?""",
                    (edit_c_name, edit_t_use, edit_t_cap, edit_t_type, edit_qty, edit_price, edit_advance, edit_r, edit_m, edit_v, selected_edit))
                db_conn.commit()
                st.success(f"✅ تم تحديث بيانات الطلبية {selected_edit} بنجاح في النظام.")
                st.rerun()

    with tab_view:
        st.write("#### 📋 كشف وجدول الطلبيات الحالية قيد التنفيذ بالمصنع")
        cursor = db_conn.cursor()
        cursor.execute("SELECT order_id, client_name, tank_use, tank_capacity, tank_type, qty, unit_price, advance_paid FROM orders")
        db_data = cursor.fetchall()
        
        if not db_data:
            st.info("لا توجد طلبيات مسجلة حالياً.")
        else:
            df_orders = pd.DataFrame(db_data, columns=[
                "كود الطلبية", "اسم العميل", "الاستخدام", "السعة الحجمية", "نوع التركيب", "الكمية المطلوبة", "سعر الوحدة (ريال)", "المقدم المدفوع (ريال)"
            ])
            st.dataframe(df_orders, use_container_width=True)

# ==========================================
# 4. قائمة التصنيع اليومي والمقارنة
# ==========================================
elif menu == "🏭 قائمة التصنيع والمقارنة":
    st.subheader("🏭 قائمة التصنيع اليومي ومراقبة الهدر")
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    
    if not all_orders:
        st.info("لا توجد طلبيات مسجلة حالياً.")
    else:
        chosen_order = st.selectbox("اختر رقم الطلبية الجاري تصنيعها لمطابقة خزانها:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (chosen_order,))
        order_data = cursor.fetchone()
        
        tank_description_str = f"خزان {order_data[2]} - سعة {order_data[3]} ({order_data[4]})"
        st.info(f"العميل الحالي: {order_data[1]} | مواصفة الإنتاج: {tank_description_str} | العدد الإجمالي المطلوب: {order_data[5]} خزان")
        
        with st.form("prod_form", clear_on_submit=True):
            col_sn1, col_sn2 = st.columns(2)
            sn_input = col_sn1.text_input("أدخل الرقم المسلسل الدقيق للخزان المنتج (مثال: ORD-101-01):")
            supervisor = col_sn2.text_input("اسم مهندس الجودة / الفني المسؤول:")
            
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
                                   (sn_input, chosen_order, tank_description_str, r_ac, m_ac, v_ac, t_ac, ca_ac, cc_ac, s_ac, str(datetime.date.today()), supervisor))
                    
                    materials_map = [
                        ("راتنج (Resin)", r_ac), ("ألياف (Mat 450)", m_ac), ("روفرز (Roving 600)", v_ac), 
                        ("تيسو (Tissue)", t_ac), ("مصلد (Catalyst)", ca_ac), ("كربونات الكالسيوم", cc_ac), ("سيليكا (Silica)", s_ac)
                    ]
                    for m_n, val in materials_map:
                        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE material_name = ?", (val, m_n))
                    db_conn.commit()
                    st.success(f"✅ تم حفظ حركة إنتاج الخزان {sn_input} وتحديث المستودع آلياً.")
                    
                    # قراءة قيم الـ BOM من قاعدة البيانات لعرض المقارنة بدقة
                    exp_vals = [order_data[8], order_data[9], order_data[10], order_data[11], order_data[12], order_data[13], order_data[14]]
                    act_vals = [r_ac, m_ac, v_ac, t_ac, ca_ac, cc_ac, s_ac]
                    diffs = [a - e for a, e in zip(act_vals, exp_vals)]
                    st.table(pd.DataFrame({"المادة الخام": raw_materials_list, "الكمية المتوقعة المحسوبة (BOM)": exp_vals, "الكمية الحقيقية المستهلكة": act_vals, "انحراف الهدر": diffs}))

# ==========================================
# 5. المشتريات والمخزن والتعديل اليدوي
# ==========================================
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 المشتريات وجرد وتصحيح أرصدة المستودع")
    t1, t2, t3 = st.tabs(["🚚 توريد خامات جديدة", "🔧 تعديل الرصيد الحالي (تصحيح أخطاء)", "📦 جرد المخزن اللحظي"])
    cursor = db_conn.cursor()
    
    with t1:
        with st.form("proc_form", clear_on_submit=True):
            supp = st.text_input("اسم المورد الأساسي:")
            mat_select = st.selectbox("المادة الموردة:", raw_materials_list)
            weight = st.number_input("الكمية المستلمة المضافة لوارد المستودع:", min_value=0.0)
            u_p = st.number_input("سعر الكيلو / الوحدة (ريال):", min_value=0.0)
            if st.form_submit_button("اعتماد دخول الشحنة للمستودع"):
                if supp and weight > 0:
                    cursor.execute("INSERT INTO procurement (supplier_name, material_name, quantity, unit_price, total_price, date) VALUES (?,?,?,?,?,?)",
                                   (supp, mat_select, weight, u_p, weight*u_p, str(datetime.date.today())))
                    cursor.execute("UPDATE inventory SET quantity = quantity + ? WHERE material_name = ?", (weight, mat_select))
                    db_conn.commit()
                    st.success("👍 تم التوريد بنجاح، ورجعت الخانات فارغة بالكامل لعملية تالية.")
                    
    with t2:
        st.write("#### ⚠️ شاشة التعديل المباشر للأرصدة (في حال الإدخال الخاطئ)")
        with st.form("adjust_form", clear_on_submit=True):
            adj_mat = st.selectbox("اختر المادة المراد إعادة ضبط رصيدها بالملي:", raw_materials_list)
            new_qty = st.number_input("أدخل الرصيد الفعلي الحقيقي الموجود بالمخزن الآن (سيستبدل القديم):", min_value=0.0)
            if st.form_submit_button("تحديث وتعديل رصيد المخزن فوراً"):
                cursor.execute("UPDATE inventory SET quantity = ? WHERE material_name = ?", (new_qty, adj_mat))
                db_conn.commit()
                st.success(f"✅ تم تصحيح رصيد مادة [{adj_mat}] ليصبح الدخل الدقيق هو: {new_qty} كجم/م2.")
                
    with t3:
        cursor.execute("SELECT * FROM inventory")
        st.dataframe(pd.DataFrame(cursor.fetchall(), columns=["المادة الخام", "الرصيد المتاح الحالي بالمستودع"]), use_container_width=True)

# ==========================================
# 6. نظام الفواتير المحسن للعملاء
# ==========================================
elif menu == "💰 الفواتير والعملاء":
    st.subheader("💰 نظام الفواتير المعتمد للعملاء")
    cursor = db_conn.cursor()
    cursor.execute("SELECT order_id FROM orders")
    all_orders = [row[0] for row in cursor.fetchall()]
    if all_orders:
        selected_o = st.selectbox("اختر رقم الطلبية المرجعية لإصدار فاتورتها الحالية:", all_orders)
        cursor.execute("SELECT * FROM orders WHERE order_id=?", (selected_o,))
        o_data = cursor.fetchone()
        
        # استرجاع القيم المحفوظة في العقد آلياً لتسهيل الحساب المالي
        sell_p = o_data[6]
        inv_mode = st.selectbox("نوع الائتمان بالفاتورة الحالية:", ["نقدي فوراً", "آجل - 30 يوماً", "آجل - 60 يوماً"])
        
        cursor.execute("SELECT COUNT(*), group_concat(serial_number) FROM production WHERE order_id=?", (selected_o,))
        prod_res = cursor.fetchone()
        done_tanks = prod_res[0] or 0
        serials_list = prod_res[1] or "لا يوجد"
        
        subtotal = done_tanks * sell_p
        vat = subtotal * 0.15
        grand_total = subtotal + vat
        remaining_balance = grand_total - o_data[7]
        
        invoice_html = f"""
        <div style="border: 3px double #1E3A8A; padding: 20px; border-radius: 5px; background-color: #fff; color: #000; direction: rtl;">
            <div style="text-align: center;">
                <h2 style="color: #1E3A8A; margin:0;">مصنع سُبُل الريادة للخزانات والمواد الصناعية</h2>
                <h4 style="background-color: #F1F5F9; padding: 5px; margin-top:5px;">فاتورة مبيعات ضريبية هندسية</h4>
            </div>
            <p><strong>السادة عملاء:</strong> {o_data[1]} | <strong>رقم الطلبية:</strong> {selected_o}</p>
            <p><strong>مواصفات الطلبية:</strong> خزان {o_data[2]} سعة {o_data[3]} ({o_data[4]})</p>
            <p><strong>نوع الفاتورة والائتمان:</strong> {inv_mode} | <strong>الأرقام المسلسلة المنتجة المشمولة:</strong> {serials_list}</p>
            <table style="width: 100%; border-collapse: collapse; text-align: center;" border="1">
                <tr style="background-color: #1E3A8A; color: white;"><th>البيان ومواصفات التوريد</th><th>الكمية المنفذة</th><th>سعر الوحدة</th><th>الإجمالي قبل الضريبة</th></tr>
                <tr><td>خزانات فايبر جلاس بمواصفات هندسية معتمدة</td><td>{done_tanks} خزان</td><td>{sell_p:,.2f} ريال</td><td>{subtotal:,.2f} ريال</td></tr>
            </table>
            <div style="float: left; width: 45%; margin-top: 15px; font-weight:bold;">
                <p>المجموع الخاضع للضريبة: {subtotal:,.2f} ريال</p>
                <p>ضريبة القيمة المضافة (15%): {vat:,.2f} ريال</p>
                <p style="color: green;">الدفعة المقدمة المحفوظة بالطلب: -{o_data[7]:,.2f} ريال</p>
                <p style="color: red; border-top: 2px solid #1E3A8A; font-size:16px;">الصافي المتبقي بمديونية العميل الكلية: {remaining_balance:,.2f} ريال</p>
            </div>
            <div style="clear:both;"></div>
            <p style="text-align: center; font-size: 11px; color:#555; margin-top:20px;">صُمم خصيصاً لمصنع سبل الريادة بواسطة المهندس محمد سلامة</p>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)

# ==========================================
# 7. رواتب العمال والمصاريف والتحليلات
# ==========================================
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
