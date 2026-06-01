import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import text

# ==========================================
# 1. الاتصال الآمن بقاعدة البيانات السحابية Neon
# ==========================================
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"🚨 خطأ في الاتصال بقاعدة البيانات: {e}")
    st.stop()

# ==========================================
# 2. دالة تنفيذ الاستعلامات
# ==========================================
def run_query(query, params=None):
    try:
        return conn.query(query, params=params, ttl=0)
    except Exception as e:
        st.error(f"خطأ في الاستعلام: {e}")
        return pd.DataFrame()

def run_write(query, params=None):
    try:
        with conn.session as session:
            session.execute(text(query), params or {})
            session.commit()
        return True
    except Exception as e:
        st.error(f"خطأ في الكتابة: {e}")
        return False

# ==========================================
# 3. قائمة المواد الخام
# ==========================================
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

# ==========================================
# 4. الهوية البصرية
# ==========================================
st.set_page_config(page_title="مصنع سُبُل الريادة - ERP v5.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .stApp {
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
    }
    .main-header { font-size: 30px; color: #1E3A8A; font-weight: bold; border-bottom: 3px solid #FBBF24; padding-bottom: 5px; }
    .designer-tag { font-size: 13px; color: #64748B; background: #F1F5F9; padding: 5px 15px; border-radius: 20px; }
    .printable-sheet { border: 2px dashed #64748B; padding: 20px; background-color: #FAFAFA; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">'
    f'<div class="main-header">🏭 نظام إدارة مصنع سُبُل الريادة - الإصدار السحابي v5.0</div>'
    f'<div class="designer-tag">تصميم المهندس محمد سلامة</div>'
    f'</div>', unsafe_allow_html=True
)

# تحذير المخزون
if st.session_state.get('global_stock_alert'):
    st.markdown('<div style="background:#EF4444;color:white;padding:15px;text-align:center;border-radius:5px;font-weight:bold;font-size:18px;margin-bottom:20px;">🚨 تحذير: المخزون لا يكفي! الرجاء شراء المواد الخام.</div>', unsafe_allow_html=True)

# القائمة الجانبية
st.sidebar.title("🛠️ العمليات والأقسام")
menu = st.sidebar.radio("انتقل إلى القسم:", [
    "📊 لوحة التحكم والميزانية",
    "📦 فتح وإدارة الطلبيات",
    "🏭 قائمة التصنيع والمقارنة",
    "📥 المشتريات والمخزن",
    "💰 الشحن والفواتير والحسابات",
    "👷 قسم العمال والأجور",
    "🔍 مركز الاستعلام المتقدم"
])

# ==========================================
# [قسم 1]: لوحة التحكم
# ==========================================
if menu == "📊 لوحة التحكم والميزانية":
    st.subheader("📈 التحليلات والتقارير المالية")

    col1, col2 = st.columns(2)
    d_start = col1.date_input("من تاريخ:", datetime.date.today() - datetime.timedelta(days=30))
    d_end = col2.date_input("إلى تاريخ:", datetime.date.today())

    st.markdown("---")

    # إجمالي المبيعات من فواتير المبيعات
    sales_df = run_query("SELECT COALESCE(SUM(grand_total),0) as total FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e", {"s": d_start, "e": d_end})
    total_sales = float(sales_df['total'].iloc[0]) if not sales_df.empty else 0.0

    # إجمالي المشتريات
    proc_df = run_query("SELECT COALESCE(SUM(total_price),0) as total FROM procurement WHERE date BETWEEN :s AND :e", {"s": d_start, "e": d_end})
    total_procurement = float(proc_df['total'].iloc[0]) if not proc_df.empty else 0.0

    # إجمالي الرواتب
    sal_df = run_query("SELECT COALESCE(SUM(net_paid),0) as total FROM worker_salaries WHERE payout_date BETWEEN :s AND :e", {"s": d_start, "e": d_end})
    total_salaries = float(sal_df['total'].iloc[0]) if not sal_df.empty else 0.0

    # إجمالي المصاريف
    exp_df = run_query("SELECT COALESCE(SUM(amount),0) as total FROM general_expenses WHERE date BETWEEN :s AND :e", {"s": d_start, "e": d_end})
    total_expenses = float(exp_df['total'].iloc[0]) if not exp_df.empty else 0.0

    total_costs = total_procurement + total_salaries + total_expenses
    net_profit = total_sales - total_costs

    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي المبيعات (ريال)", f"{total_sales:,.2f}")
    c2.metric("إجمالي التكاليف (ريال)", f"{total_costs:,.2f}")
    c3.metric("صافي الربح (ريال)", f"{net_profit:,.2f}", delta="ربح" if net_profit >= 0 else "خسارة")

    st.markdown("---")
    st.write("### 📦 الطلبيات النشطة حالياً")
    active_orders = run_query("SELECT order_id, status, qty, total_price FROM orders WHERE status = 'قيد التنفيذ'")
    if not active_orders.empty:
        st.dataframe(active_orders, use_container_width=True)
    else:
        st.info("لا توجد طلبيات نشطة حالياً.")

    st.write("### 🏪 أرصدة المخزن الحالية")
    inv_df = run_query("SELECT material_name, quantity FROM inventory ORDER BY material_name")
    if not inv_df.empty:
        st.dataframe(inv_df, use_container_width=True)

# ==========================================
# [قسم 2]: الطلبيات
# ==========================================
elif menu == "📦 فتح وإدارة الطلبيات":
    st.subheader("📦 منظومة التحكم وحسابات الطلبيات")
    t_new, t_edit, t_active = st.tabs(["➕ فتح طلبية جديدة", "📝 تعديل طلبية", "📋 الطلبيات الجارية"])

    with t_new:
        st.write("#### ➕ تأسيس طلبية جديدة")
        auto_order_code = f"SUBUL-ORD-{datetime.date.today().year}-{random.randint(1000,9999)}"
        st.info(f"🤖 كود الطلبية المقترح: **{auto_order_code}**")
        order_id_input = st.text_input("كود الطلبية (يمكن تعديله):", value=auto_order_code)

        # إضافة عميل جديد
        with st.expander("👤 تسجيل عميل جديد أولاً؟"):
            cust_trade = st.text_input("اسم العميل التجاري:")
            cust_cr = st.text_input("رقم السجل التجاري:")
            cust_tax = st.text_input("الرقم الضريبي:")
            if st.button("حفظ العميل"):
                if cust_trade:
                    ok = run_write("INSERT INTO customers (trade_name, cr_number, tax_number) VALUES (:t, :c, :tx) ON CONFLICT (trade_name) DO NOTHING", {"t": cust_trade, "c": cust_cr, "tx": cust_tax})
                    if ok:
                        st.success(f"✅ تم تسجيل العميل [{cust_trade}] بنجاح!")

        # اختيار عميل
        customers_df = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
        if customers_df.empty:
            st.warning("لا يوجد عملاء. أضف عميلاً أولاً.")
        else:
            cust_options = customers_df['trade_name'].tolist()
            selected_customer = st.selectbox("اختر العميل:", cust_options)
            customer_id = int(customers_df[customers_df['trade_name'] == selected_customer]['id'].iloc[0])

            c1, c2, c3 = st.columns(3)
            t_use = c1.selectbox("استخدام الخزان:", ["ماء", "صرف", "ديزل", "حريق"])
            t_capacity = c2.text_input("سعة الخزان:")
            t_type = c3.selectbox("نوع الخزان:", ["دفّان", "فوق الأرض"])

            c4, c5 = st.columns(2)
            qty_input = c4.number_input("عدد الخزانات:", min_value=1, value=10)
            unit_price_input = c5.number_input("سعر الخزان الواحد (ريال):", min_value=0.0, value=3500.0)

            total_order_val = qty_input * unit_price_input
            advance_mode = st.selectbox("طريقة المقدم:", ["مبلغ بالريال", "نسبة مئوية (%)"])
            advance_value = st.number_input("قيمة المقدم:", min_value=0.0, value=0.0)

            if advance_mode == "نسبة مئوية (%)":
                net_advance = (total_order_val * advance_value) / 100
            else:
                net_advance = advance_value

            remaining_val = total_order_val - net_advance

            st.markdown(f"""
            <div style="background:#F8FAFC;padding:15px;border-radius:5px;border-right:4px solid #1E3A8A;font-weight:bold;">
            💰 إجمالي العقد: {total_order_val:,.2f} ريال | 🟢 المقدم: {net_advance:,.2f} ريال | 🔴 المتبقي: {remaining_val:,.2f} ريال
            </div>
            """, unsafe_allow_html=True)

            st.write("---")
            st.markdown("**📋 كميات المواد المعيارية لخزان واحد:**")
            cx1, cx2, cx3 = st.columns(3)
            r_ex = cx1.number_input("راتنج (كجم):", min_value=0.0, value=250.0)
            m_ex = cx2.number_input("ألياف Mat (كجم):", min_value=0.0, value=80.0)
            v_ex = cx3.number_input("روفرز (كجم):", min_value=0.0, value=40.0)
            t_ex = cx1.number_input("تيسو (م²):", min_value=0.0, value=12.0)
            ca_ex = cx2.number_input("مصلد (كجم):", min_value=0.0, value=4.0)
            cc_ex = cx3.number_input("كالسيوم (كجم):", min_value=0.0, value=100.0)
            s_ex = cx1.number_input("سيليكا (كجم):", min_value=0.0, value=8.0)

            # فحص المخزون الحقيقي
            inv_df = run_query("SELECT material_name, quantity FROM inventory")
            inv_dict = dict(zip(inv_df['material_name'], inv_df['quantity'])) if not inv_df.empty else {}

            resin_key = "راتنج كميائي صنف اول للديزل" if t_use == "ديزل" else "راتنج كميائي صنف ٢ للصرف الصحي"
            available_resin = inv_dict.get(resin_key, 0)
            required_resin = r_ex * qty_input

            if required_resin > available_resin:
                st.error(f"⚠️ نقص في الراتنج! المطلوب: {required_resin} كجم | المتاح: {available_resin} كجم | العجز: {required_resin - available_resin} كجم")
                st.session_state['global_stock_alert'] = True

            if st.button("🚀 اعتماد الطلبية وحفظها"):
                ok = run_write("""
                    INSERT INTO orders (order_id, customer_id, tank_use, tank_capacity, tank_type, qty, unit_price, total_price, advance_paid, remaining_balance, resin_exp, mat_exp, roving_exp, tissue_exp, catalyst_exp, calcium_exp, silica_exp)
                    VALUES (:oid, :cid, :tu, :tc, :tt, :qty, :up, :tp, :ap, :rb, :re, :me, :ve, :te, :cae, :cce, :se)
                """, {
                    "oid": order_id_input, "cid": customer_id, "tu": t_use, "tc": t_capacity, "tt": t_type,
                    "qty": qty_input, "up": unit_price_input, "tp": total_order_val, "ap": net_advance,
                    "rb": remaining_val, "re": r_ex, "me": m_ex, "ve": v_ex, "te": t_ex,
                    "cae": ca_ex, "cce": cc_ex, "se": s_ex
                })
                if ok:
                    st.session_state['global_stock_alert'] = False
                    st.success("✅ تم حفظ الطلبية بنجاح في قاعدة البيانات!")
                    st.rerun()

    with t_edit:
        st.write("#### 📝 تعديل طلبية قائمة")
        orders_df = run_query("SELECT o.order_id, c.trade_name, o.qty, o.status FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'قيد التنفيذ'")
        if orders_df.empty:
            st.info("لا توجد طلبيات للتعديل.")
        else:
            order_list = [f"{r['order_id']} | {r['trade_name']}" for _, r in orders_df.iterrows()]
            selected_edit = st.selectbox("اختر الطلبية:", order_list)
            selected_oid = selected_edit.split(" | ")[0]
            new_status = st.selectbox("الحالة الجديدة:", ["قيد التنفيذ", "مكتملة", "ملغاة"])
            if st.button("💾 حفظ التعديل"):
                ok = run_write("UPDATE orders SET status = :s WHERE order_id = :oid", {"s": new_status, "oid": selected_oid})
                if ok:
                    st.success("✅ تم تحديث الطلبية بنجاح!")

    with t_active:
        st.write("#### 📋 الطلبيات الجارية")
        active_df = run_query("""
            SELECT o.order_id, c.trade_name as العميل, o.tank_use as الاستخدام,
                   o.qty as الكمية, o.total_price as القيمة, o.status as الحالة
            FROM orders o JOIN customers c ON o.customer_id = c.id
            WHERE o.status = 'قيد التنفيذ'
        """)
        if active_df.empty:
            st.info("لا توجد طلبيات جارية.")
        else:
            st.dataframe(active_df, use_container_width=True)

# ==========================================
# [قسم 3]: التصنيع
# ==========================================
elif menu == "🏭 قائمة التصنيع والمقارنة":
    st.subheader("🏭 إدارة صالة الإنتاج")

    orders_df = run_query("""
        SELECT o.order_id, c.trade_name, o.qty,
               o.resin_exp, o.mat_exp, o.roving_exp, o.tissue_exp,
               o.catalyst_exp, o.calcium_exp, o.silica_exp
        FROM orders o JOIN customers c ON o.customer_id = c.id
        WHERE o.status = 'قيد التنفيذ'
    """)

    if orders_df.empty:
        st.info("لا توجد طلبيات جارية للتصنيع.")
    else:
        order_options = [f"{r['order_id']} | {r['trade_name']} | {r['qty']} خزان" for _, r in orders_df.iterrows()]
        selected_prod = st.selectbox("اختر الطلبية:", order_options)
        selected_oid = selected_prod.split(" | ")[0]
        order_row = orders_df[orders_df['order_id'] == selected_oid].iloc[0]

        tanks_today = st.number_input("عدد الخزانات المستهدفة اليوم:", min_value=1, value=2)

        # حساب الصرف المعياري
        calc_resin = tanks_today * float(order_row['resin_exp'] or 0)
        calc_mat = tanks_today * float(order_row['mat_exp'] or 0)
        calc_roving = tanks_today * float(order_row['roving_exp'] or 0)
        calc_tissue = tanks_today * float(order_row['tissue_exp'] or 0)
        calc_catalyst = tanks_today * float(order_row['catalyst_exp'] or 0)
        calc_calcium = tanks_today * float(order_row['calcium_exp'] or 0)
        calc_silica = tanks_today * float(order_row['silica_exp'] or 0)

        st.markdown(f"""
        <div class="printable-sheet">
        <h4 style="text-align:center;color:#1E3A8A;">📋 مستند صرف مواد - {selected_oid}</h4>
        <p>عدد الخزانات: {tanks_today} | التاريخ: {datetime.date.today()}</p>
        <ul>
            <li>راتنج: <b>{calc_resin} كجم</b></li>
            <li>ألياف Mat: <b>{calc_mat} كجم</b></li>
            <li>روفرز: <b>{calc_roving} كجم</b></li>
            <li>تيسو: <b>{calc_tissue} م²</b></li>
            <li>مصلد: <b>{calc_catalyst} كجم</b></li>
            <li>كالسيوم: <b>{calc_calcium} كجم</b></li>
            <li>سيليكا: <b>{calc_silica} كجم</b></li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🎬 بدء وردية جديدة وخصم المواد من المخزن"):
            # خصم المواد من المخزن
            updates = [
                ("راتنج كميائي صنف اول للديزل", calc_resin),
                ("ألياف (Mat 450)", calc_mat),
                ("روفرز (Roving 600)", calc_roving),
                ("تيسو (Tissue)", calc_tissue),
                ("مصلد (Catalyst)", calc_catalyst),
                ("كربونات الكالسيوم", calc_calcium),
                ("سيليكا (Silica)", calc_silica),
            ]
            for mat, qty in updates:
                run_write("UPDATE inventory SET quantity = quantity - :q WHERE material_name = :m", {"q": qty, "m": mat})

            # إنشاء سجل وردية
            ok = run_write("INSERT INTO production_days (order_id, planned_qty, date) VALUES (:oid, :pq, :d)",
                           {"oid": selected_oid, "pq": tanks_today, "d": datetime.date.today()})
            if ok:
                st.success("✅ تم فتح الوردية وخصم المواد من المخزن!")

        st.write("---")
        st.markdown("### 🔒 إنهاء الوردية وتسجيل الإنتاج الفعلي")
        tanks_actual = st.number_input("عدد الخزانات المنفذة فعلياً:", min_value=0, value=tanks_today)
        supervisor = st.text_input("اسم المشرف:")

        if st.button("🔒 إنهاء الوردية وتسجيل الأرقام المسلسلة"):
            # جيب آخر وردية
            last_shift = run_query("SELECT id FROM production_days WHERE order_id = :oid ORDER BY id DESC LIMIT 1", {"oid": selected_oid})
            if not last_shift.empty:
                shift_id = int(last_shift['id'].iloc[0])
                run_write("UPDATE production_days SET actual_qty = :aq, status = 'مغلق' WHERE id = :sid", {"aq": tanks_actual, "sid": shift_id})

                for i in range(1, tanks_actual + 1):
                    serial = f"SUBUL-SN-{datetime.date.today().year}-{random.randint(10000,99999)}-{i:02d}"
                    run_write("""
                        INSERT INTO production_tanks (serial_number, order_id, shift_id, prod_date, supervisor)
                        VALUES (:sn, :oid, :sid, :pd, :sup)
                    """, {"sn": serial, "oid": selected_oid, "sid": shift_id, "pd": datetime.date.today(), "sup": supervisor})
                    st.markdown(f"✅ تم تسجيل الخزان: `{serial}`")

                st.success(f"🏁 تم إغلاق الوردية وتسجيل {tanks_actual} خزان بنجاح!")

# ==========================================
# [قسم 4]: المشتريات والمخزن
# ==========================================
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 إدارة المشتريات والمخزن")
    t_supp, t_buy, t_adj, t_stock = st.tabs(["🤝 مورد جديد", "🚚 فاتورة توريد", "🔧 ضبط الأرصدة", "📊 رصيد المخزن"])

    with t_supp:
        st.write("#### 🤝 تسجيل مورد جديد")
        with st.form("supplier_form", clear_on_submit=True):
            s_orig = st.text_input("اسم المورد الأصلي:")
            s_trade = st.text_input("الاسم التجاري:")
            s_cr = st.text_input("رقم السجل التجاري:")
            if st.form_submit_button("حفظ المورد"):
                if s_orig:
                    ok = run_write("INSERT INTO suppliers (original_name, trade_name, cr_number) VALUES (:o, :t, :c) ON CONFLICT (original_name) DO NOTHING", {"o": s_orig, "t": s_trade, "c": s_cr})
                    if ok:
                        st.success(f"✅ تم تسجيل المورد [{s_orig}]!")

    with t_buy:
        st.write("#### 🚚 تسجيل فاتورة توريد جديدة")
        suppliers_df = run_query("SELECT id, original_name FROM suppliers ORDER BY original_name")
        if suppliers_df.empty:
            st.warning("أضف موردين أولاً.")
        else:
            sup_options = suppliers_df['original_name'].tolist()
            chosen_sup = st.selectbox("اختر المورد:", sup_options)
            sup_id = int(suppliers_df[suppliers_df['original_name'] == chosen_sup]['id'].iloc[0])

            with st.form("buy_form", clear_on_submit=True):
                mat_sel = st.selectbox("المادة الخام:", raw_materials_list)
                sup_qty = st.number_input("الكمية المستلمة:", min_value=0.0, value=1000.0)
                sup_price = st.number_input("سعر الوحدة (ريال):", min_value=0.0, value=8.5)
                total_proc = sup_qty * sup_price

                if st.form_submit_button("اعتماد الفاتورة وإضافة للمخزن"):
                    ok1 = run_write("INSERT INTO procurement (supplier_id, material_name, quantity, unit_price, total_price) VALUES (:sid, :m, :q, :up, :tp)",
                                    {"sid": sup_id, "m": mat_sel, "q": sup_qty, "up": sup_price, "tp": total_proc})
                    ok2 = run_write("UPDATE inventory SET quantity = quantity + :q WHERE material_name = :m", {"q": sup_qty, "m": mat_sel})
                    if ok1 and ok2:
                        st.success(f"✅ تم إضافة {sup_qty} من [{mat_sel}] للمخزن! قيمة الفاتورة: {total_proc:,.2f} ريال")

    with t_adj:
        st.write("#### 🔧 ضبط رصيد مادة يدوياً")
        with st.form("adj_form", clear_on_submit=True):
            mat_adj = st.selectbox("اختر المادة:", raw_materials_list)
            new_qty = st.number_input("الرصيد الجديد الدقيق:", min_value=0.0)
            if st.form_submit_button("تحديث الرصيد"):
                ok = run_write("UPDATE inventory SET quantity = :q WHERE material_name = :m", {"q": new_qty, "m": mat_adj})
                if ok:
                    st.success(f"✅ تم تحديث رصيد [{mat_adj}] إلى {new_qty}")

    with t_stock:
        st.write("#### 📊 أرصدة المخزن الحالية")
        inv_df = run_query("SELECT material_name as المادة, quantity as الكمية FROM inventory ORDER BY material_name")
        if not inv_df.empty:
            st.dataframe(inv_df, use_container_width=True)
        else:
            st.info("المخزن فارغ.")

# ==========================================
# [قسم 5]: الشحن والفواتير
# ==========================================
elif menu == "💰 الشحن والفواتير والحسابات":
    st.subheader("💰 منظومة الشحن والفواتير والحسابات")
    t_ship, t_inv, t_pay, t_stmt = st.tabs(["🚚 أمر تسليم", "📄 فاتورة ضريبية", "🏦 سند قبض", "🔍 كشف حساب"])

    with t_ship:
        st.write("#### 🚚 إصدار أمر تسليم")
        orders_df = run_query("SELECT o.order_id, c.trade_name FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'قيد التنفيذ'")
        if orders_df.empty:
            st.info("لا توجد طلبيات.")
        else:
            order_opts = [f"{r['order_id']} | {r['trade_name']}" for _, r in orders_df.iterrows()]
            sel_ship = st.selectbox("اختر الطلبية:", order_opts)
            sel_oid = sel_ship.split(" | ")[0]
            shipped_qty = st.number_input("عدد الخزانات المشحونة:", min_value=1, value=5)
            d_name = st.text_input("اسم السائق:")
            d_plate = st.text_input("رقم اللوحة:")
            d_iqama = st.text_input("رقم الإقامة:")

            if st.button("🚀 إصدار أمر التسليم"):
                ok = run_write("INSERT INTO delivery_orders (order_id, shipped_qty, driver_name, car_plate, driver_iqama) VALUES (:oid, :sq, :dn, :dp, :di)",
                               {"oid": sel_oid, "sq": shipped_qty, "dn": d_name, "dp": d_plate, "di": d_iqama})
                if ok:
                    qr_hash = f"SUBUL-{random.randint(100000,999999)}"
                    st.markdown(f"""
                    <div class="printable-sheet">
                    <h3 style="text-align:center;">🏭 أمر تسليم - مصنع سُبُل الريادة</h3>
                    <p><b>الطلبية:</b> {sel_oid} | <b>التاريخ:</b> {datetime.date.today()}</p>
                    <p><b>السائق:</b> {d_name} | <b>اللوحة:</b> {d_plate} | <b>الإقامة:</b> {d_iqama}</p>
                    <p><b>الكمية المشحونة:</b> {shipped_qty} خزان</p>
                    <p style="text-align:center;border:2px solid #000;padding:10px;">QR: {qr_hash}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.success("✅ تم إصدار أمر التسليم وحفظه!")

    with t_inv:
        st.write("#### 📄 إصدار فاتورة ضريبية")
        deliveries_df = run_query("""
            SELECT d.delivery_id, d.order_id, d.shipped_qty, o.unit_price, o.advance_paid, o.qty
            FROM delivery_orders d JOIN orders o ON d.order_id = o.order_id
        """)
        if deliveries_df.empty:
            st.info("لا توجد أوامر تسليم.")
        else:
            del_opts = [f"أمر رقم {r['delivery_id']} - {r['order_id']} - {r['shipped_qty']} خزان" for _, r in deliveries_df.iterrows()]
            sel_del = st.selectbox("اختر أمر التسليم:", del_opts)
            del_id = int(sel_del.split(" ")[2])
            del_row = deliveries_df[deliveries_df['delivery_id'] == del_id].iloc[0]

            subtotal = float(del_row['shipped_qty']) * float(del_row['unit_price'])
            advance_ratio = float(del_row['advance_paid']) / float(del_row['qty']) if float(del_row['qty']) > 0 else 0
            advance_deducted = advance_ratio * float(del_row['shipped_qty'])
            vat = subtotal * 0.15
            grand_total = subtotal + vat
            net_required = grand_total - advance_deducted

            st.markdown(f"""
            <div class="printable-sheet">
            <h3 style="text-align:center;color:#1E3A8A;">فاتورة ضريبية رسمية</h3>
            <p>المبلغ قبل الضريبة: <b>{subtotal:,.2f} ريال</b></p>
            <p>ضريبة 15%: <b>{vat:,.2f} ريال</b></p>
            <p>الإجمالي: <b>{grand_total:,.2f} ريال</b></p>
            <p style="color:green;">خصم المقدم: <b>-{advance_deducted:,.2f} ريال</b></p>
            <h4 style="color:red;">الصافي المستحق: {net_required:,.2f} ريال</h4>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💾 حفظ الفاتورة"):
                ok = run_write("""
                    INSERT INTO sales_invoices (delivery_id, order_id, subtotal, vat, grand_total, advance_deducted, net_required)
                    VALUES (:did, :oid, :st, :v, :gt, :ad, :nr)
                """, {"did": del_id, "oid": del_row['order_id'], "st": subtotal, "v": vat, "gt": grand_total, "ad": advance_deducted, "nr": net_required})
                if ok:
                    st.success("✅ تم حفظ الفاتورة بنجاح!")

    with t_pay:
        st.write("#### 🏦 تسجيل سند قبض")
        customers_df = run_query("SELECT id, trade_name FROM customers")
        orders_df2 = run_query("SELECT order_id FROM orders WHERE status = 'قيد التنفيذ'")
        if not customers_df.empty:
            cust_opts = customers_df['trade_name'].tolist()
            sel_cust = st.selectbox("العميل:", cust_opts)
            cust_id = int(customers_df[customers_df['trade_name'] == sel_cust]['id'].iloc[0])

            if not orders_df2.empty:
                sel_ord = st.selectbox("الطلبية:", orders_df2['order_id'].tolist())
            else:
                sel_ord = st.text_input("كود الطلبية:")

            pay_amt = st.number_input("المبلغ المستلم (ريال):", min_value=0.0, value=0.0)
            pay_type = st.selectbox("طريقة الدفع:", ["نقدي", "تحويل بنكي", "شبكة مدى"])
            bank = st.text_input("اسم البنك (إن وجد):")

            if st.button("💵 اعتماد سند القبض"):
                ok = run_write("INSERT INTO customer_payments (customer_id, order_id, amount, payment_type, bank_name) VALUES (:cid, :oid, :a, :pt, :b)",
                               {"cid": cust_id, "oid": sel_ord, "a": pay_amt, "pt": pay_type, "b": bank})
                if ok:
                    st.success(f"✅ تم تسجيل سند القبض بمبلغ {pay_amt:,.2f} ريال!")

    with t_stmt:
        st.write("#### 🔍 كشف حساب عميل")
        customers_df = run_query("SELECT id, trade_name FROM customers")
        if not customers_df.empty:
            sel_cust = st.selectbox("اختر العميل:", customers_df['trade_name'].tolist(), key="stmt_cust")
            cust_id = int(customers_df[customers_df['trade_name'] == sel_cust]['id'].iloc[0])

            if st.button("📊 عرض كشف الحساب"):
                payments_df = run_query("""
                    SELECT payment_date as التاريخ, payment_type as النوع, amount as المبلغ, bank_name as البنك
                    FROM customer_payments WHERE customer_id = :cid ORDER BY payment_date DESC
                """, {"cid": cust_id})

                invoices_df = run_query("""
                    SELECT si.invoice_date as التاريخ, si.grand_total as الإجمالي, si.net_required as المستحق
                    FROM sales_invoices si JOIN orders o ON si.order_id = o.order_id
                    WHERE o.customer_id = :cid ORDER BY si.invoice_date DESC
                """, {"cid": cust_id})

                col1, col2 = st.columns(2)
                with col1:
                    st.write("**المدفوعات:**")
                    st.dataframe(payments_df if not payments_df.empty else pd.DataFrame(), use_container_width=True)
                with col2:
                    st.write("**الفواتير:**")
                    st.dataframe(invoices_df if not invoices_df.empty else pd.DataFrame(), use_container_width=True)

                total_paid = float(payments_df['المبلغ'].sum()) if not payments_df.empty else 0.0
                total_due = float(invoices_df['المستحق'].sum()) if not invoices_df.empty else 0.0
                balance = total_due - total_paid
                st.metric("الرصيد المستحق على العميل (ريال)", f"{balance:,.2f}")

# ==========================================
# [قسم 6]: العمال والأجور
# ==========================================
elif menu == "👷 قسم العمال والأجور":
    st.subheader("👷 منظومة كادر العمال والأجور")
    t_add, t_adv, t_sal, t_query = st.tabs(["👤 إضافة عامل", "💵 سلفة", "💰 مسير الراتب", "🔍 استعلام"])

    with t_add:
        with st.form("worker_form", clear_on_submit=True):
            w_name = st.text_input("اسم العامل:")
            w_iqama = st.text_input("رقم الإقامة:")
            w_start = st.date_input("تاريخ بداية العمل:")
            if st.form_submit_button("حفظ العامل"):
                if w_name and w_iqama:
                    ok = run_write("INSERT INTO workers (name, iqama_id, start_date) VALUES (:n, :i, :s) ON CONFLICT (iqama_id) DO NOTHING",
                                   {"n": w_name, "i": w_iqama, "s": w_start})
                    if ok:
                        st.success(f"✅ تم تسجيل العامل [{w_name}]!")

    with t_adv:
        workers_df = run_query("SELECT id, name, iqama_id FROM workers ORDER BY name")
        if workers_df.empty:
            st.info("لا يوجد عمال.")
        else:
            w_opts = [f"{r['name']} - {r['iqama_id']}" for _, r in workers_df.iterrows()]
            sel_w = st.selectbox("اختر العامل:", w_opts)
            sel_wid = int(workers_df[workers_df['name'] == sel_w.split(" - ")[0]]['id'].iloc[0])
            adv_amt = st.number_input("مبلغ السلفة:", min_value=0.0, value=1000.0)

            if st.button("💵 اعتماد السلفة"):
                ok = run_write("INSERT INTO worker_advances (worker_id, amount) VALUES (:wid, :a)", {"wid": sel_wid, "a": adv_amt})
                if ok:
                    st.success(f"✅ تم صرف سلفة {adv_amt:,.2f} ريال!")

    with t_sal:
        workers_df = run_query("SELECT id, name FROM workers ORDER BY name")
        if not workers_df.empty:
            sel_w = st.selectbox("اختر العامل:", workers_df['name'].tolist(), key="sal_w")
            wid = int(workers_df[workers_df['name'] == sel_w]['id'].iloc[0])

            # حساب السلف المستحقة
            adv_df = run_query("SELECT COALESCE(SUM(amount),0) as total FROM worker_advances WHERE worker_id = :wid AND status = 'قيد الانتظار'", {"wid": wid})
            total_advances = float(adv_df['total'].iloc[0]) if not adv_df.empty else 0.0

            base_salary = st.number_input("الراتب الأساسي:", min_value=0.0, value=5000.0)
            month_year = st.text_input("الشهر والسنة (مثال: 2026-06):", value=datetime.date.today().strftime("%Y-%m"))
            net_salary = base_salary - total_advances

            st.markdown(f"""
            <div class="printable-sheet">
            <h4 style="text-align:center;color:green;">إيصال راتب - {sel_w}</h4>
            <p>الراتب الأساسي: <b>{base_salary:,.2f} ريال</b></p>
            <p style="color:red;">خصم السلف: <b>-{total_advances:,.2f} ريال</b></p>
            <h4>الصافي: {net_salary:,.2f} ريال</h4>
            </div>
            """, unsafe_allow_html=True)

            if st.button("💰 اعتماد مسير الراتب"):
                ok = run_write("INSERT INTO worker_salaries (worker_id, month_year, base_salary, advances_deducted, net_paid) VALUES (:wid, :my, :bs, :ad, :np)",
                               {"wid": wid, "my": month_year, "bs": base_salary, "ad": total_advances, "np": net_salary})
                if ok:
                    # تحديث حالة السلف
                    run_write("UPDATE worker_advances SET status = 'مخصومة' WHERE worker_id = :wid AND status = 'قيد الانتظار'", {"wid": wid})
                    st.success(f"✅ تم اعتماد راتب {sel_w} بصافي {net_salary:,.2f} ريال!")

    with t_query:
        search = st.text_input("ابحث باسم العامل أو رقم الإقامة:")
        if search:
            result = run_query("SELECT name as الاسم, iqama_id as الإقامة, start_date as تاريخ_البداية FROM workers WHERE name ILIKE :s OR iqama_id LIKE :s2",
                               {"s": f"%{search}%", "s2": f"%{search}%"})
            st.dataframe(result if not result.empty else pd.DataFrame({"النتيجة": ["لا يوجد نتائج"]}), use_container_width=True)

# ==========================================
# [قسم 7]: الاستعلام المتقدم
# ==========================================
elif menu == "🔍 مركز الاستعلام المتقدم":
    st.subheader("🔍 بوابة البحث والاستعلامات")

    query_type = st.selectbox("نوع الاستعلام:", [
        "البحث عن عميل",
        "تتبع طلبية",
        "حساب مورد",
        "سجل خزان بالرقم المسلسل"
    ])

    keyword = st.text_input("أدخل كلمة البحث:")

    if st.button("🔍 بحث") and keyword:
        if query_type == "البحث عن عميل":
            df = run_query("SELECT trade_name, cr_number, tax_number FROM customers WHERE trade_name ILIKE :k", {"k": f"%{keyword}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة": ["لا يوجد نتائج"]}), use_container_width=True)

        elif query_type == "تتبع طلبية":
            df = run_query("""
                SELECT o.order_id, c.trade_name, o.qty, o.total_price, o.status, o.order_date
                FROM orders o JOIN customers c ON o.customer_id = c.id
                WHERE o.order_id ILIKE :k OR c.trade_name ILIKE :k
            """, {"k": f"%{keyword}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة": ["لا يوجد نتائج"]}), use_container_width=True)

        elif query_type == "حساب مورد":
            df = run_query("""
                SELECT p.date, p.material_name, p.quantity, p.unit_price, p.total_price, s.original_name
                FROM procurement p JOIN suppliers s ON p.supplier_id = s.id
                WHERE s.original_name ILIKE :k OR s.trade_name ILIKE :k
            """, {"k": f"%{keyword}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة": ["لا يوجد نتائج"]}), use_container_width=True)

        elif query_type == "سجل خزان بالرقم المسلسل":
            df = run_query("""
                SELECT pt.serial_number, pt.order_id, pt.prod_date, pt.supervisor,
                       pt.resin_act, pt.mat_act, pt.roving_act
                FROM production_tanks pt
                WHERE pt.serial_number ILIKE :k
            """, {"k": f"%{keyword}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة": ["لا يوجد نتائج"]}), use_container_width=True)
