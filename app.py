import streamlit as st
import pandas as pd
import datetime
import random
import io
from sqlalchemy import text

# ==========================================
# 1. الاتصال بقاعدة البيانات
# ==========================================
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error(f"🚨 خطأ في الاتصال: {e}")
    st.stop()

def run_query(query, params=None):
    try:
        return conn.query(query, params=params, ttl=0)
    except Exception as e:
        st.error(f"خطأ: {e}")
        return pd.DataFrame()

def run_write(query, params=None):
    try:
        with conn.session as session:
            session.execute(text(query), params or {})
            session.commit()
        return True
    except Exception as e:
        st.error(f"خطأ: {e}")
        return False

# ==========================================
# 2. بيانات المصنع
# ==========================================
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

# ==========================================
# 3. الهوية البصرية
# ==========================================
st.set_page_config(page_title="مصنع سُبُل الريادة - ERP v6.0", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [data-testid="stSidebar"], .stApp { font-family: 'Cairo', sans-serif; direction: RTL; text-align: right; }
.main-header { font-size: 28px; color: #1E3A8A; font-weight: bold; border-bottom: 3px solid #FBBF24; padding-bottom: 5px; }
.designer-tag { font-size: 12px; color: #64748B; background: #F1F5F9; padding: 4px 12px; border-radius: 20px; }
.print-card { border: 1.5px solid #CBD5E1; padding: 20px; background: #fff; border-radius: 8px; margin: 10px 0; }
.alert-red { background:#EF4444; color:white; padding:12px; text-align:center; border-radius:5px; font-weight:bold; margin-bottom:15px; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:15px;">'
    f'<div class="main-header">🏭 {FACTORY_NAME} — نظام ERP v6.0</div>'
    f'<div class="designer-tag">تصميم المهندس محمد سلامة</div>'
    f'</div>', unsafe_allow_html=True
)

if st.session_state.get('global_stock_alert'):
    st.markdown('<div class="alert-red">🚨 تحذير: المخزون لا يكفي! يرجى شراء المواد الخام فوراً.</div>', unsafe_allow_html=True)

# ==========================================
# 4. القائمة الجانبية
# ==========================================
st.sidebar.title("🛠️ الأقسام والعمليات")
menu = st.sidebar.radio("انتقل إلى:", [
    "📊 لوحة التحكم",
    "📦 الطلبيات",
    "🏭 التصنيع",
    "📥 المشتريات والمخزن",
    "💰 الشحن والفواتير",
    "👷 العمال والأجور",
    "🔍 الاستعلام المتقدم",
    "🗑️ حذف كامل للبيانات"
])

# ==========================================
# دالة مساعدة: تحويل DataFrame لـ CSV
# ==========================================
def df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def print_header():
    return f"""
    <div style="text-align:center; border-bottom:2px solid #1E3A8A; padding-bottom:10px; margin-bottom:15px;">
        <h2 style="color:#1E3A8A; margin:0;">{FACTORY_NAME}</h2>
        <p style="margin:2px 0; color:#555;">{FACTORY_ADDRESS}</p>
        <p style="margin:2px 0; color:#555; font-size:13px;">س.ت: {FACTORY_CR} | الرقم الضريبي: {FACTORY_TAX}</p>
    </div>
    """

# ==========================================
# [قسم 1]: لوحة التحكم
# ==========================================
if menu == "📊 لوحة التحكم":
    st.subheader("📈 لوحة التحكم والتقارير المالية")
    c1, c2 = st.columns(2)
    d_start = c1.date_input("من:", datetime.date.today() - datetime.timedelta(days=30))
    d_end = c2.date_input("إلى:", datetime.date.today())
    st.markdown("---")

    total_sales = float(run_query("SELECT COALESCE(SUM(grand_total),0) as t FROM sales_invoices WHERE invoice_date BETWEEN :s AND :e", {"s":d_start,"e":d_end})['t'].iloc[0])
    total_proc = float(run_query("SELECT COALESCE(SUM(total_price),0) as t FROM procurement WHERE date BETWEEN :s AND :e", {"s":d_start,"e":d_end})['t'].iloc[0])
    total_sal = float(run_query("SELECT COALESCE(SUM(net_paid),0) as t FROM worker_salaries WHERE payout_date BETWEEN :s AND :e", {"s":d_start,"e":d_end})['t'].iloc[0])
    total_exp = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM general_expenses WHERE date BETWEEN :s AND :e", {"s":d_start,"e":d_end})['t'].iloc[0])
    total_costs = total_proc + total_sal + total_exp
    net_profit = total_sales - total_costs

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("إجمالي المبيعات", f"{total_sales:,.2f} ر")
    m2.metric("إجمالي المشتريات", f"{total_proc:,.2f} ر")
    m3.metric("الرواتب والمصاريف", f"{total_sal+total_exp:,.2f} ر")
    m4.metric("صافي الربح/الخسارة", f"{net_profit:,.2f} ر", delta="ربح" if net_profit>=0 else "خسارة")

    st.markdown("---")
    st.write("### 📦 الطلبيات النشطة")
    adf = run_query("SELECT o.order_id, c.trade_name as العميل, o.qty as الكمية, o.total_price as القيمة, o.status as الحالة FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
    st.dataframe(adf if not adf.empty else pd.DataFrame({"الحالة":["لا توجد طلبيات نشطة"]}), use_container_width=True)

    st.write("### 🏪 المخزن الحالي")
    inv = run_query("SELECT material_name as المادة, quantity as الكمية FROM inventory ORDER BY material_name")
    st.dataframe(inv if not inv.empty else pd.DataFrame(), use_container_width=True)

# ==========================================
# [قسم 2]: الطلبيات
# ==========================================
elif menu == "📦 الطلبيات":
    st.subheader("📦 منظومة الطلبيات")
    tabs = st.tabs(["➕ طلبية جديدة", "📝 تعديل طلبية", "📋 الطلبيات الجارية", "💵 دفعات عميل", "🔍 استعلام عميل"])

    # ---- تبويب 1: طلبية جديدة ----
    with tabs[0]:
        if 'order_form_key' not in st.session_state:
            st.session_state.order_form_key = 0

        with st.form(f"order_form_{st.session_state.order_form_key}", clear_on_submit=True):
            st.write("#### ➕ فتح طلبية جديدة")
            auto_code = f"SUBUL-ORD-{datetime.date.today().year}-{random.randint(1000,9999)}"
            order_id_f = st.text_input("كود الطلبية:", value=auto_code)

            customers_df = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
            if customers_df.empty:
                st.warning("أضف عملاء أولاً من قسم الاستعلام.")
                cust_sel = None
            else:
                cust_sel = st.selectbox("العميل:", customers_df['trade_name'].tolist())

            c1,c2,c3 = st.columns(3)
            t_use = c1.selectbox("استخدام الخزان:", ["ماء","صرف","ديزل","حريق"])
            t_cap = c2.text_input("السعة (مثال: 10,000 لتر):")
            t_typ = c3.selectbox("نوع التركيب:", ["دفّان","فوق الأرض"])

            c4,c5 = st.columns(2)
            qty_f = c4.number_input("عدد الخزانات:", min_value=1, value=10)
            uprice_f = c5.number_input("سعر الخزان الواحد (ريال):", min_value=0.0, value=3500.0)
            total_val = qty_f * uprice_f

            adv_mode = st.selectbox("طريقة المقدم:", ["مبلغ بالريال","نسبة مئوية (%)"])
            adv_val = st.number_input("قيمة المقدم:", min_value=0.0, value=0.0)
            net_adv = (total_val * adv_val / 100) if adv_mode == "نسبة مئوية (%)" else adv_val
            remaining = total_val - net_adv

            st.markdown(f"💰 **إجمالي العقد:** {total_val:,.2f} | 🟢 **المقدم:** {net_adv:,.2f} | 🔴 **المتبقي:** {remaining:,.2f}")

            st.write("---")
            st.markdown("**كميات المواد المعيارية لخزان واحد:**")
            x1,x2,x3 = st.columns(3)
            r_ex = x1.number_input("راتنج (كجم):", min_value=0.0, value=250.0)
            m_ex = x2.number_input("ألياف Mat (كجم):", min_value=0.0, value=80.0)
            v_ex = x3.number_input("روفرز (كجم):", min_value=0.0, value=40.0)
            t_ex = x1.number_input("تيسو (م²):", min_value=0.0, value=12.0)
            ca_ex = x2.number_input("مصلد (كجم):", min_value=0.0, value=4.0)
            cc_ex = x3.number_input("كالسيوم (كجم):", min_value=0.0, value=100.0)
            s_ex = x1.number_input("سيليكا (كجم):", min_value=0.0, value=8.0)

            st.markdown(f"""
            **📊 إجمالي المواد للطلبية كاملة ({qty_f} خزان):**
            راتنج: {r_ex*qty_f:.1f} كجم | ألياف: {m_ex*qty_f:.1f} كجم | روفرز: {v_ex*qty_f:.1f} كجم |
            تيسو: {t_ex*qty_f:.1f} م² | مصلد: {ca_ex*qty_f:.1f} كجم | كالسيوم: {cc_ex*qty_f:.1f} كجم | سيليكا: {s_ex*qty_f:.1f} كجم
            """)

            submitted = st.form_submit_button("🚀 حفظ الطلبية")
            if submitted and cust_sel:
                cid = int(customers_df[customers_df['trade_name']==cust_sel]['id'].iloc[0])
                ok = run_write("""
                    INSERT INTO orders (order_id,customer_id,tank_use,tank_capacity,tank_type,qty,unit_price,total_price,advance_paid,remaining_balance,resin_exp,mat_exp,roving_exp,tissue_exp,catalyst_exp,calcium_exp,silica_exp)
                    VALUES (:oid,:cid,:tu,:tc,:tt,:qty,:up,:tp,:ap,:rb,:re,:me,:ve,:te,:cae,:cce,:se)
                """, {"oid":order_id_f,"cid":cid,"tu":t_use,"tc":t_cap,"tt":t_typ,"qty":qty_f,"up":uprice_f,
                      "tp":total_val,"ap":net_adv,"rb":remaining,"re":r_ex,"me":m_ex,"ve":v_ex,
                      "te":t_ex,"cae":ca_ex,"cce":cc_ex,"se":s_ex})
                if ok:
                    st.success("✅ تم حفظ الطلبية!")
                    st.session_state.order_form_key += 1
                    st.rerun()

    # ---- تبويب 2: تعديل طلبية ----
    with tabs[1]:
        orders_df = run_query("SELECT o.order_id, c.trade_name, o.qty, o.status FROM orders o JOIN customers c ON o.customer_id=c.id")
        if orders_df.empty:
            st.info("لا توجد طلبيات.")
        else:
            sel = st.selectbox("اختر الطلبية:", [f"{r['order_id']} | {r['trade_name']}" for _,r in orders_df.iterrows()])
            oid = sel.split(" | ")[0]
            new_status = st.selectbox("الحالة:", ["قيد التنفيذ","مكتملة","ملغاة"])
            if st.button("💾 حفظ التعديل"):
                if run_write("UPDATE orders SET status=:s WHERE order_id=:oid", {"s":new_status,"oid":oid}):
                    st.success("✅ تم تحديث الطلبية!")

    # ---- تبويب 3: الطلبيات الجارية ----
    with tabs[2]:
        adf = run_query("""SELECT o.order_id as "رقم الطلبية", c.trade_name as "العميل", o.tank_use as "الاستخدام",
            o.qty as "الكمية", o.total_price as "القيمة الإجمالية", o.advance_paid as "المقدم",
            o.remaining_balance as "المتبقي", o.status as "الحالة", o.order_date as "التاريخ"
            FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'""")
        st.dataframe(adf if not adf.empty else pd.DataFrame({"الحالة":["لا توجد طلبيات جارية"]}), use_container_width=True)
        if not adf.empty:
            st.download_button("⬇️ تنزيل التقرير", df_to_csv(adf), "active_orders.csv", "text/csv")

    # ---- تبويب 4: دفعات عميل ----
    with tabs[3]:
        st.write("#### 💵 تسجيل دفعة من عميل")
        customers_df2 = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
        if not customers_df2.empty:
            sel_c = st.selectbox("اسم العميل:", customers_df2['trade_name'].tolist(), key="pay_cust")
            cid2 = int(customers_df2[customers_df2['trade_name']==sel_c]['id'].iloc[0])
            orders_df2 = run_query("SELECT order_id FROM orders WHERE customer_id=:cid AND status='قيد التنفيذ'", {"cid":cid2})
            if not orders_df2.empty:
                sel_ord = st.selectbox("رقم الطلبية:", orders_df2['order_id'].tolist(), key="pay_ord")
                del_df = run_query("SELECT delivery_id FROM delivery_orders WHERE order_id=:oid", {"oid":sel_ord})
                del_opts = ["—"] + [str(x) for x in del_df['delivery_id'].tolist()] if not del_df.empty else ["—"]
                sel_del = st.selectbox("رقم أمر التسليم (اختياري):", del_opts, key="pay_del")
                pay_amt = st.number_input("مبلغ الدفعة (ريال):", min_value=0.0, value=0.0, key="pay_amt")
                pay_type = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"], key="pay_type")
                bank = st.text_input("اسم البنك (إن وجد):", key="pay_bank")
                if st.button("💵 اعتماد الدفعة"):
                    ok = run_write("INSERT INTO customer_payments (customer_id,order_id,amount,payment_type,bank_name) VALUES (:cid,:oid,:a,:pt,:b)",
                                   {"cid":cid2,"oid":sel_ord,"a":pay_amt,"pt":pay_type,"b":bank})
                    if ok:
                        st.success(f"✅ تم تسجيل دفعة {pay_amt:,.2f} ريال!")
            else:
                st.info("لا توجد طلبيات جارية لهذا العميل.")

    # ---- تبويب 5: استعلام عميل ----
    with tabs[4]:
        st.write("#### 🔍 كشف حساب عميل")
        customers_df3 = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
        if not customers_df3.empty:
            sel_c3 = st.selectbox("اختر العميل:", customers_df3['trade_name'].tolist(), key="stmt_c")
            cid3 = int(customers_df3[customers_df3['trade_name']==sel_c3]['id'].iloc[0])
            d1,d2 = st.columns(2)
            ds = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="stmt_ds")
            de = d2.date_input("إلى:", datetime.date.today(), key="stmt_de")
            if st.button("📊 عرض كشف الحساب"):
                inv_df = run_query("""SELECT si.invoice_date as "التاريخ", si.invoice_id as "رقم الفاتورة",
                    o.order_id as "الطلبية", si.grand_total as "إجمالي الفاتورة", si.net_required as "المستحق"
                    FROM sales_invoices si JOIN orders o ON si.order_id=o.order_id
                    WHERE o.customer_id=:cid AND si.invoice_date BETWEEN :s AND :e ORDER BY si.invoice_date""",
                    {"cid":cid3,"s":ds,"e":de})
                pay_df = run_query("""SELECT payment_date as "التاريخ", order_id as "الطلبية",
                    amount as "المبلغ المدفوع", payment_type as "طريقة الدفع", bank_name as "البنك"
                    FROM customer_payments WHERE customer_id=:cid AND payment_date BETWEEN :s AND :e ORDER BY payment_date""",
                    {"cid":cid3,"s":ds,"e":de})
                total_inv = float(inv_df['المستحق'].sum()) if not inv_df.empty else 0.0
                total_paid = float(pay_df['المبلغ المدفوع'].sum()) if not pay_df.empty else 0.0
                balance = total_inv - total_paid

                st.markdown(f"""<div class="print-card">{print_header()}
                <h3 style="text-align:center;">كشف حساب عميل: {sel_c3}</h3>
                <p>الفترة: {ds} إلى {de}</p></div>""", unsafe_allow_html=True)
                st.write("**الفواتير:**"); st.dataframe(inv_df if not inv_df.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True)
                st.write("**المدفوعات:**"); st.dataframe(pay_df if not pay_df.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True)
                m1,m2,m3 = st.columns(3)
                m1.metric("إجمالي الفواتير", f"{total_inv:,.2f} ر")
                m2.metric("إجمالي المدفوع", f"{total_paid:,.2f} ر")
                m3.metric("الرصيد المستحق", f"{balance:,.2f} ر")
                combined = pd.concat([inv_df, pay_df], ignore_index=True) if not inv_df.empty or not pay_df.empty else pd.DataFrame()
                if not combined.empty:
                    st.download_button("⬇️ تنزيل كشف الحساب", df_to_csv(combined), f"stmt_{sel_c3}.csv", "text/csv")

# ==========================================
# [قسم 3]: التصنيع
# ==========================================
elif menu == "🏭 التصنيع":
    st.subheader("🏭 إدارة صالة الإنتاج")
    orders_df = run_query("""SELECT o.order_id, c.trade_name, o.qty,
        o.resin_exp,o.mat_exp,o.roving_exp,o.tissue_exp,o.catalyst_exp,o.calcium_exp,o.silica_exp
        FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'""")
    if orders_df.empty:
        st.info("لا توجد طلبيات جارية."); st.stop()

    opts = [f"{r['order_id']} | {r['trade_name']} | {r['qty']} خزان" for _,r in orders_df.iterrows()]
    sel = st.selectbox("اختر الطلبية:", opts)
    oid = sel.split(" | ")[0]
    row = orders_df[orders_df['order_id']==oid].iloc[0]

    tanks_today = st.number_input("عدد الخزانات المستهدفة اليوم:", min_value=1, value=2)

    # حساب المواد
    calc = {
        "راتنج": tanks_today * float(row['resin_exp'] or 0),
        "ألياف Mat": tanks_today * float(row['mat_exp'] or 0),
        "روفرز": tanks_today * float(row['roving_exp'] or 0),
        "تيسو": tanks_today * float(row['tissue_exp'] or 0),
        "مصلد": tanks_today * float(row['catalyst_exp'] or 0),
        "كالسيوم": tanks_today * float(row['calcium_exp'] or 0),
        "سيليكا": tanks_today * float(row['silica_exp'] or 0),
    }

    dispatch_html = f"""
    <div class="print-card" id="dispatch_doc" style="color:black;">
    {print_header()}
    <h3 style="text-align:center;color:black;">أمر صرف مواد خام من المخزن</h3>
    <p style="color:black;"><b>الطلبية:</b> {oid} | <b>التاريخ:</b> {datetime.date.today()} | <b>عدد الخزانات:</b> {tanks_today}</p>
    <table style="width:100%;border-collapse:collapse;color:black;" border="1">
    <tr style="background:#1E3A8A;color:white;"><th>المادة</th><th>الكمية المطلوبة</th><th>الوحدة</th></tr>
    {"".join(f'<tr><td style="color:black;">{k}</td><td style="color:black;">{v:.2f}</td><td style="color:black;">كجم/م²</td></tr>' for k,v in calc.items())}
    </table>
    <p style="margin-top:20px;color:black;">توقيع أمين المخزن: ......................... | توقيع مدير الإنتاج: .........................</p>
    </div>"""
    st.markdown(dispatch_html, unsafe_allow_html=True)

    dispatch_df = pd.DataFrame(list(calc.items()), columns=["المادة","الكمية"])
    st.download_button("⬇️ تنزيل أمر الصرف", df_to_csv(dispatch_df), f"dispatch_{oid}_{datetime.date.today()}.csv", "text/csv")

    if st.button("🎬 بدء الوردية وخصم المواد من المخزن"):
        mat_keys = {
            "راتنج كميائي صنف اول للديزل": calc["راتنج"],
            "ألياف (Mat 450)": calc["ألياف Mat"],
            "روفرز (Roving 600)": calc["روفرز"],
            "تيسو (Tissue)": calc["تيسو"],
            "مصلد (Catalyst)": calc["مصلد"],
            "كربونات الكالسيوم": calc["كالسيوم"],
            "سيليكا (Silica)": calc["سيليكا"],
        }
        for mat, qty in mat_keys.items():
            run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m", {"q":qty,"m":mat})
        ok = run_write("INSERT INTO production_days (order_id,planned_qty,date) VALUES (:oid,:pq,:d)", {"oid":oid,"pq":tanks_today,"d":datetime.date.today()})
        if ok:
            st.success("✅ تم فتح الوردية وخصم المواد!")

    st.write("---")
    st.markdown("### 🔒 إنهاء الوردية")
    actual_qty = st.number_input("العدد الفعلي المصنَّع:", min_value=0, value=int(tanks_today))
    supervisor = st.text_input("اسم المشرف:")

    if st.button("🔒 إنهاء الوردية وتوليد الأرقام المسلسلة"):
        last_shift = run_query("SELECT id FROM production_days WHERE order_id=:oid ORDER BY id DESC LIMIT 1", {"oid":oid})
        if not last_shift.empty:
            shift_id = int(last_shift['id'].iloc[0])
            run_write("UPDATE production_days SET actual_qty=:aq,status='مغلق' WHERE id=:sid", {"aq":actual_qty,"sid":shift_id})

            serials = []
            for i in range(1, actual_qty+1):
                sn = f"SUBUL-SN-{datetime.date.today().year}-{random.randint(10000,99999)}-{i:02d}"
                run_write("INSERT INTO production_tanks (serial_number,order_id,shift_id,prod_date,supervisor) VALUES (:sn,:oid,:sid,:pd,:sup)",
                          {"sn":sn,"oid":oid,"sid":shift_id,"pd":datetime.date.today(),"sup":supervisor})
                serials.append(sn)
                st.markdown(f"🔹 خزان {i}: `{sn}`")

            st.success(f"✅ تم إغلاق الوردية وتسجيل {actual_qty} خزان!")

            # مقارنة المواد
            st.write("### 📊 تقرير المقارنة")
            planned_total = {k: tanks_today * v for k, v in [
                ("راتنج", float(row['resin_exp'] or 0)),
                ("ألياف Mat", float(row['mat_exp'] or 0)),
                ("روفرز", float(row['roving_exp'] or 0)),
            ]}
            actual_resin = actual_qty * float(row['resin_exp'] or 0)
            dev = actual_resin - calc["راتنج"]

            if dev > 0:
                st.warning(f"⚠️ زيادة استهلاك راتنج: {dev:.2f} كجم — سيتم خصمها من المخزن.")
                run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name='راتنج كميائي صنف اول للديزل'", {"q":dev})
            elif dev < 0:
                st.success(f"🟢 وفر في الراتنج: {abs(dev):.2f} كجم — تمت إضافتها للمخزن.")
                run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name='راتنج كميائي صنف اول للديزل'", {"q":abs(dev)})

# ==========================================
# [قسم 4]: المشتريات والمخزن
# ==========================================
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 المشتريات والمخزن")
    tabs = st.tabs(["🤝 مورد جديد", "🚚 فاتورة توريد", "💳 دفعات مورد", "🔍 كشف حساب مورد", "🔧 ضبط المخزن", "📊 رصيد المخزن"])

    # ---- تبويب 1: مورد جديد ----
    with tabs[0]:
        with st.form("sup_form", clear_on_submit=True):
            s_orig = st.text_input("اسم المورد الأصلي:")
            s_trade = st.text_input("الاسم التجاري:")
            s_cr = st.text_input("رقم السجل التجاري:")
            if st.form_submit_button("حفظ المورد"):
                if s_orig:
                    if run_write("INSERT INTO suppliers (original_name,trade_name,cr_number) VALUES (:o,:t,:c) ON CONFLICT (original_name) DO NOTHING", {"o":s_orig,"t":s_trade,"c":s_cr}):
                        st.success(f"✅ تم تسجيل المورد [{s_orig}]!")

    # ---- تبويب 2: فاتورة توريد (متعددة البنود) ----
    with tabs[1]:
        st.write("#### 🚚 تسجيل فاتورة توريد جديدة")
        suppliers_df = run_query("SELECT id, original_name FROM suppliers ORDER BY original_name")
        if suppliers_df.empty:
            st.warning("أضف موردين أولاً.")
        else:
            chosen_sup = st.selectbox("اختر المورد:", suppliers_df['original_name'].tolist(), key="proc_sup")
            sup_id = int(suppliers_df[suppliers_df['original_name']==chosen_sup]['id'].iloc[0])
            inv_num = st.text_input("رقم الفاتورة:", key="proc_inv_num")
            pay_type_proc = st.selectbox("نوع الدفع:", ["آجل","نقدي","دفع جزئي"], key="proc_pay_type")

            st.markdown("**أضف بنود الفاتورة:**")
            if 'proc_items' not in st.session_state:
                st.session_state.proc_items = []

            with st.form("add_item_form", clear_on_submit=True):
                ci1,ci2,ci3 = st.columns(3)
                mat_sel = ci1.selectbox("المادة:", raw_materials_list, key="item_mat")
                item_qty = ci2.number_input("الكمية:", min_value=0.0, value=0.0, key="item_qty")
                item_price = ci3.number_input("سعر الوحدة:", min_value=0.0, value=0.0, key="item_price")
                if st.form_submit_button("➕ إضافة البند"):
                    st.session_state.proc_items.append({"المادة":mat_sel,"الكمية":item_qty,"سعر الوحدة":item_price,"الإجمالي":item_qty*item_price})
                    st.success(f"تمت إضافة: {mat_sel}")

            if st.session_state.proc_items:
                items_df = pd.DataFrame(st.session_state.proc_items)
                st.dataframe(items_df, use_container_width=True)
                subtotal = items_df['الإجمالي'].sum()
                vat = subtotal * 0.15
                grand = subtotal + vat
                entered_total = st.number_input("القيمة الإجمالية للفاتورة (للتحقق):", min_value=0.0, value=grand, key="entered_total")

                st.markdown(f"المجموع قبل الضريبة: **{subtotal:,.2f}** | ضريبة 15%: **{vat:,.2f}** | الإجمالي المحسوب: **{grand:,.2f}**")
                diff = abs(entered_total - grand)
                if diff > 1:
                    st.warning(f"⚠️ فرق بين القيمة المدخلة والمحسوبة: {diff:,.2f} ريال — تحقق من الفاتورة.")
                else:
                    st.success("✅ القيمة الإجمالية مطابقة مع الضريبة.")

                if st.button("✅ اعتماد الفاتورة وإضافة للمخزن"):
                    if not inv_num:
                        st.error("أدخل رقم الفاتورة أولاً!")
                    else:
                        for item in st.session_state.proc_items:
                            run_write("INSERT INTO procurement (supplier_id,material_name,quantity,unit_price,total_price) VALUES (:sid,:m,:q,:up,:tp)",
                                      {"sid":sup_id,"m":item['المادة'],"q":item['الكمية'],"up":item['سعر الوحدة'],"tp":item['الإجمالي']})
                            run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name=:m", {"q":item['الكمية'],"m":item['المادة']})
                        st.success(f"✅ تم اعتماد الفاتورة {inv_num} وتحديث المخزن!")
                        st.session_state.proc_items = []
                        st.rerun()

                if st.button("🗑️ مسح البنود"):
                    st.session_state.proc_items = []
                    st.rerun()

    # ---- تبويب 3: دفعات مورد ----
    with tabs[2]:
        st.write("#### 💳 تسجيل دفعة لمورد")
        suppliers_df2 = run_query("SELECT id, original_name FROM suppliers ORDER BY original_name")
        if not suppliers_df2.empty:
            sel_sup = st.selectbox("اسم المورد:", suppliers_df2['original_name'].tolist(), key="spay_sup")
            sup_id2 = int(suppliers_df2[suppliers_df2['original_name']==sel_sup]['id'].iloc[0])
            proc_df = run_query("SELECT id, material_name, total_price FROM procurement WHERE supplier_id=:sid ORDER BY date DESC", {"sid":sup_id2})
            if not proc_df.empty:
                proc_opts = [f"فاتورة #{r['id']} - {r['material_name']} - {r['total_price']:,.2f} ر" for _,r in proc_df.iterrows()]
                sel_proc = st.selectbox("رقم الفاتورة:", proc_opts, key="spay_proc")
                proc_id = int(sel_proc.split("#")[1].split(" ")[0])
                spay_amt = st.number_input("المبلغ المدفوع:", min_value=0.0, value=0.0, key="spay_amt")
                spay_type = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي"], key="spay_type")
                spay_bank = st.text_input("اسم البنك:", key="spay_bank")

                if st.button("💳 اعتماد الدفعة"):
                    ok = run_write("INSERT INTO customer_payments (customer_id,order_id,amount,payment_type,bank_name) VALUES (:cid,:oid,:a,:pt,:b)",
                                   {"cid":0,"oid":f"PROC-{proc_id}","a":spay_amt,"pt":spay_type,"b":spay_bank})
                    if ok:
                        proc_row = proc_df[proc_df['id']==proc_id].iloc[0]
                        total_paid_so_far = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM customer_payments WHERE order_id=:oid", {"oid":f"PROC-{proc_id}"})['t'].iloc[0])
                        remaining_proc = float(proc_row['total_price']) * 1.15 - total_paid_so_far
                        st.success(f"✅ تم تسجيل الدفعة!")
                        st.markdown(f"""<div class="print-card">
                        {print_header()}
                        <h3 style="text-align:center;">إيصال دفع لمورد</h3>
                        <p><b>المورد:</b> {sel_sup} | <b>رقم الفاتورة:</b> #{proc_id}</p>
                        <p><b>المبلغ المدفوع:</b> {spay_amt:,.2f} ريال | <b>طريقة الدفع:</b> {spay_type}</p>
                        <p><b>المتبقي على الفاتورة:</b> {remaining_proc:,.2f} ريال</p>
                        <p>التاريخ: {datetime.date.today()}</p>
                        </div>""", unsafe_allow_html=True)

    # ---- تبويب 4: كشف حساب مورد ----
    with tabs[3]:
        st.write("#### 🔍 كشف حساب مورد")
        suppliers_df3 = run_query("SELECT id, original_name FROM suppliers ORDER BY original_name")
        if not suppliers_df3.empty:
            sel_sup3 = st.selectbox("اختر المورد:", suppliers_df3['original_name'].tolist(), key="sstmt_sup")
            sup_id3 = int(suppliers_df3[suppliers_df3['original_name']==sel_sup3]['id'].iloc[0])
            d1,d2 = st.columns(2)
            ds3 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="sstmt_ds")
            de3 = d2.date_input("إلى:", datetime.date.today(), key="sstmt_de")
            if st.button("📊 عرض كشف المورد"):
                proc_hist = run_query("""SELECT date as "التاريخ", material_name as "المادة", quantity as "الكمية",
                    unit_price as "سعر الوحدة", total_price as "قيمة الفاتورة"
                    FROM procurement WHERE supplier_id=:sid AND date BETWEEN :s AND :e ORDER BY date""",
                    {"sid":sup_id3,"s":ds3,"e":de3})
                total_invoices = float(proc_hist['قيمة الفاتورة'].sum()) * 1.15 if not proc_hist.empty else 0.0
                pay_hist = run_query("""SELECT payment_date as "التاريخ", amount as "المدفوع", payment_type as "الطريقة"
                    FROM customer_payments cp
                    WHERE cp.order_id LIKE 'PROC-%' AND cp.payment_date BETWEEN :s AND :e""",
                    {"s":ds3,"e":de3})
                total_paid = float(pay_hist['المدفوع'].sum()) if not pay_hist.empty else 0.0
                balance = total_invoices - total_paid

                st.markdown(f"""<div class="print-card">{print_header()}
                <h3 style="text-align:center;">كشف حساب مورد: {sel_sup3}</h3>
                <p>الفترة: {ds3} إلى {de3}</p></div>""", unsafe_allow_html=True)
                st.write("**الفواتير:**"); st.dataframe(proc_hist if not proc_hist.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True)
                st.write("**المدفوعات:**"); st.dataframe(pay_hist if not pay_hist.empty else pd.DataFrame({"الحالة":["لا توجد"]}), use_container_width=True)
                m1,m2,m3 = st.columns(3)
                m1.metric("إجمالي الفواتير (مع ضريبة)", f"{total_invoices:,.2f} ر")
                m2.metric("إجمالي المدفوع", f"{total_paid:,.2f} ر")
                m3.metric("المستحق للمورد", f"{balance:,.2f} ر")
                if not proc_hist.empty:
                    st.download_button("⬇️ تنزيل كشف الحساب", df_to_csv(proc_hist), f"supplier_stmt_{sel_sup3}.csv", "text/csv")

    # ---- تبويب 5: ضبط المخزن ----
    with tabs[4]:
        with st.form("adj_form", clear_on_submit=True):
            mat_adj = st.selectbox("المادة:", raw_materials_list)
            new_qty = st.number_input("الرصيد الجديد:", min_value=0.0)
            if st.form_submit_button("تحديث الرصيد"):
                if run_write("UPDATE inventory SET quantity=:q WHERE material_name=:m", {"q":new_qty,"m":mat_adj}):
                    st.success(f"✅ تم تحديث رصيد [{mat_adj}] إلى {new_qty}")

    # ---- تبويب 6: رصيد المخزن ----
    with tabs[5]:
        inv_df = run_query("SELECT material_name as المادة, quantity as الكمية FROM inventory ORDER BY material_name")
        st.dataframe(inv_df if not inv_df.empty else pd.DataFrame(), use_container_width=True)
        if not inv_df.empty:
            st.download_button("⬇️ تنزيل رصيد المخزن", df_to_csv(inv_df), "inventory.csv", "text/csv")

# ==========================================
# [قسم 5]: الشحن والفواتير
# ==========================================
elif menu == "💰 الشحن والفواتير":
    st.subheader("💰 الشحن والفواتير الضريبية")
    tabs = st.tabs(["🚚 أمر تسليم", "📄 فاتورة ضريبية", "🏦 سند قبض", "🔍 استعلام فواتير"])

    with tabs[0]:
        orders_df = run_query("SELECT o.order_id, c.trade_name, o.qty, c.cr_number, c.tax_number FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
        if orders_df.empty:
            st.info("لا توجد طلبيات.")
        else:
            sel = st.selectbox("الطلبية:", [f"{r['order_id']} | {r['trade_name']}" for _,r in orders_df.iterrows()])
            oid = sel.split(" | ")[0]
            ord_row = orders_df[orders_df['order_id']==oid].iloc[0]
            shipped = st.number_input("عدد الخزانات المشحونة:", min_value=1, value=5)
            d_name = st.text_input("اسم السائق:")
            d_plate = st.text_input("رقم اللوحة:")
            d_iqama = st.text_input("رقم الإقامة:")

            if st.button("🚀 إصدار أمر التسليم"):
                ok = run_write("INSERT INTO delivery_orders (order_id,shipped_qty,driver_name,car_plate,driver_iqama) VALUES (:oid,:sq,:dn,:dp,:di)",
                               {"oid":oid,"sq":shipped,"dn":d_name,"dp":d_plate,"di":d_iqama})
                if ok:
                    new_del = run_query("SELECT delivery_id FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_id DESC LIMIT 1", {"oid":oid})
                    del_id = int(new_del['delivery_id'].iloc[0]) if not new_del.empty else "—"
                    qr = f"SUBUL-{random.randint(100000,999999)}"
                    do_html = f"""<div class="print-card" style="color:black;">
                    {print_header()}
                    <h3 style="text-align:center;color:black;">أمر تسليم رقم: {del_id}</h3>
                    <p style="color:black;"><b>الطلبية:</b> {oid} | <b>العميل:</b> {ord_row['trade_name']} | <b>التاريخ:</b> {datetime.date.today()}</p>
                    <p style="color:black;"><b>السائق:</b> {d_name} | <b>اللوحة:</b> {d_plate} | <b>الإقامة:</b> {d_iqama}</p>
                    <p style="color:black;"><b>الكمية المشحونة:</b> {shipped} خزان</p>
                    <div style="border:2px solid #000;padding:10px;width:200px;margin:10px auto;text-align:center;color:black;">
                    QR: {qr}</div>
                    <p style="color:black;">توقيع مراقب البوابة: .........................</p>
                    </div>"""
                    st.markdown(do_html, unsafe_allow_html=True)
                    do_df = pd.DataFrame([{"أمر التسليم":del_id,"الطلبية":oid,"العميل":ord_row['trade_name'],"الكمية":shipped,"السائق":d_name,"اللوحة":d_plate,"التاريخ":datetime.date.today()}])
                    st.download_button("⬇️ تنزيل أمر التسليم", df_to_csv(do_df), f"DO_{del_id}.csv", "text/csv")
                    st.success(f"✅ تم إصدار أمر التسليم #{del_id}!")

    with tabs[1]:
        deliveries_df = run_query("""SELECT d.delivery_id, d.order_id, d.shipped_qty, d.delivery_date,
            o.unit_price, o.advance_paid, o.qty as total_qty, c.trade_name, c.cr_number, c.tax_number
            FROM delivery_orders d JOIN orders o ON d.order_id=o.order_id JOIN customers c ON o.customer_id=c.id""")
        if deliveries_df.empty:
            st.info("لا توجد أوامر تسليم.")
        else:
            del_opts = [f"أمر #{r['delivery_id']} | {r['order_id']} | {r['trade_name']} | {r['shipped_qty']} خزان" for _,r in deliveries_df.iterrows()]
            sel_del = st.selectbox("اختر أمر التسليم:", del_opts)
            del_id = int(sel_del.split("#")[1].split(" ")[0])
            dr = deliveries_df[deliveries_df['delivery_id']==del_id].iloc[0]

            subtotal = float(dr['shipped_qty']) * float(dr['unit_price'])
            adv_per_tank = float(dr['advance_paid']) / float(dr['total_qty']) if float(dr['total_qty']) > 0 else 0
            adv_deducted = adv_per_tank * float(dr['shipped_qty'])
            vat = subtotal * 0.15
            grand = subtotal + vat
            net = grand - adv_deducted
            inv_num = f"INV-{del_id}-{datetime.date.today().strftime('%Y%m%d')}"

            inv_html = f"""<div class="print-card" style="color:black;">
            {print_header()}
            <h3 style="text-align:center;color:black;">فاتورة ضريبية رسمية</h3>
            <p style="color:black;"><b>رقم الفاتورة:</b> {inv_num} | <b>التاريخ:</b> {datetime.date.today()}</p>
            <p style="color:black;"><b>العميل:</b> {dr['trade_name']} | <b>السجل التجاري:</b> {dr['cr_number']} | <b>الرقم الضريبي:</b> {dr['tax_number']}</p>
            <table style="width:100%;border-collapse:collapse;color:black;" border="1">
            <tr style="background:#1E3A8A;color:white;"><th>البيان</th><th>الكمية</th><th>سعر الوحدة</th><th>الإجمالي</th></tr>
            <tr style="color:black;"><td>خزانات فايبر جلاس</td><td>{dr['shipped_qty']}</td><td>{float(dr['unit_price']):,.2f}</td><td>{subtotal:,.2f}</td></tr>
            </table>
            <p style="color:black;">المجموع قبل الضريبة: <b>{subtotal:,.2f} ريال</b></p>
            <p style="color:black;">ضريبة القيمة المضافة 15%: <b>{vat:,.2f} ريال</b></p>
            <p style="color:black;">الإجمالي شامل الضريبة: <b>{grand:,.2f} ريال</b></p>
            <p style="color:green;">خصم المقدم: <b>-{adv_deducted:,.2f} ريال</b></p>
            <h3 style="color:red;">الصافي المستحق: {net:,.2f} ريال</h3>
            </div>"""
            st.markdown(inv_html, unsafe_allow_html=True)

            inv_df_dl = pd.DataFrame([{"رقم الفاتورة":inv_num,"العميل":dr['trade_name'],"الكمية":dr['shipped_qty'],"الإجمالي":grand,"الصافي المستحق":net,"التاريخ":datetime.date.today()}])
            st.download_button("⬇️ تنزيل الفاتورة", df_to_csv(inv_df_dl), f"{inv_num}.csv", "text/csv")

            if st.button("💾 حفظ الفاتورة في النظام"):
                ok = run_write("""INSERT INTO sales_invoices (delivery_id,order_id,subtotal,vat,grand_total,advance_deducted,net_required)
                    VALUES (:did,:oid,:st,:v,:gt,:ad,:nr)""",
                    {"did":del_id,"oid":dr['order_id'],"st":subtotal,"v":vat,"gt":grand,"ad":adv_deducted,"nr":net})
                if ok:
                    st.success(f"✅ تم حفظ الفاتورة {inv_num}!")

    with tabs[2]:
        customers_df = run_query("SELECT id, trade_name FROM customers")
        if not customers_df.empty:
            sel_c = st.selectbox("العميل:", customers_df['trade_name'].tolist(), key="rcpt_c")
            cid = int(customers_df[customers_df['trade_name']==sel_c]['id'].iloc[0])
            orders_df2 = run_query("SELECT order_id FROM orders WHERE customer_id=:cid", {"cid":cid})
            sel_ord = st.selectbox("الطلبية:", orders_df2['order_id'].tolist() if not orders_df2.empty else ["—"])
            pay_amt = st.number_input("المبلغ (ريال):", min_value=0.0, value=0.0)
            pay_type = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"])
            bank = st.text_input("البنك:")
            if st.button("💵 اعتماد السند"):
                if run_write("INSERT INTO customer_payments (customer_id,order_id,amount,payment_type,bank_name) VALUES (:cid,:oid,:a,:pt,:b)",
                             {"cid":cid,"oid":sel_ord,"a":pay_amt,"pt":pay_type,"b":bank}):
                    st.success(f"✅ تم تسجيل {pay_amt:,.2f} ريال!")

    with tabs[3]:
        st.write("#### 🔍 استعلام فواتير")
        customers_df4 = run_query("SELECT id, trade_name FROM customers")
        if not customers_df4.empty:
            sel_c4 = st.selectbox("العميل:", ["الكل"] + customers_df4['trade_name'].tolist(), key="inv_query_c")
            d1,d2 = st.columns(2)
            ds4 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="inv_ds")
            de4 = d2.date_input("إلى:", datetime.date.today(), key="inv_de")
            if st.button("🔍 بحث عن الفواتير"):
                if sel_c4 == "الكل":
                    inv_res = run_query("""SELECT si.invoice_id, si.invoice_date, o.order_id, c.trade_name as العميل,
                        si.grand_total, si.net_required FROM sales_invoices si
                        JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id
                        WHERE si.invoice_date BETWEEN :s AND :e ORDER BY si.invoice_date DESC""", {"s":ds4,"e":de4})
                else:
                    cid4 = int(customers_df4[customers_df4['trade_name']==sel_c4]['id'].iloc[0])
                    inv_res = run_query("""SELECT si.invoice_id, si.invoice_date, o.order_id, c.trade_name as العميل,
                        si.grand_total, si.net_required FROM sales_invoices si
                        JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id
                        WHERE o.customer_id=:cid AND si.invoice_date BETWEEN :s AND :e ORDER BY si.invoice_date DESC""",
                        {"cid":cid4,"s":ds4,"e":de4})
                st.dataframe(inv_res if not inv_res.empty else pd.DataFrame({"الحالة":["لا توجد فواتير"]}), use_container_width=True)
                if not inv_res.empty:
                    st.download_button("⬇️ تنزيل الفواتير", df_to_csv(inv_res), "invoices.csv", "text/csv")

# ==========================================
# [قسم 6]: العمال والأجور
# ==========================================
elif menu == "👷 العمال والأجور":
    st.subheader("👷 منظومة العمال والأجور")
    tabs = st.tabs(["👤 إضافة عامل", "💵 سلفة", "💰 مسير الراتب", "🔍 استعلام"])

    with tabs[0]:
        with st.form("w_form", clear_on_submit=True):
            w_name = st.text_input("الاسم:")
            w_iq = st.text_input("رقم الإقامة:")
            w_st = st.date_input("تاريخ الالتحاق:")
            if st.form_submit_button("حفظ"):
                if w_name and w_iq:
                    if run_write("INSERT INTO workers (name,iqama_id,start_date) VALUES (:n,:i,:s) ON CONFLICT (iqama_id) DO NOTHING", {"n":w_name,"i":w_iq,"s":w_st}):
                        st.success(f"✅ تم تسجيل [{w_name}]!")

    with tabs[1]:
        wdf = run_query("SELECT id, name, iqama_id FROM workers ORDER BY name")
        if not wdf.empty:
            w_sel = st.selectbox("العامل:", [f"{r['name']} - {r['iqama_id']}" for _,r in wdf.iterrows()])
            wid = int(wdf[wdf['name']==w_sel.split(" - ")[0]]['id'].iloc[0])
            adv = st.number_input("مبلغ السلفة:", min_value=0.0, value=1000.0)
            if st.button("💵 اعتماد"):
                if run_write("INSERT INTO worker_advances (worker_id,amount) VALUES (:w,:a)", {"w":wid,"a":adv}):
                    st.success(f"✅ تم صرف {adv:,.2f} ريال!")

    with tabs[2]:
        wdf2 = run_query("SELECT id, name FROM workers ORDER BY name")
        if not wdf2.empty:
            w_sel2 = st.selectbox("العامل:", wdf2['name'].tolist(), key="sal_w")
            wid2 = int(wdf2[wdf2['name']==w_sel2]['id'].iloc[0])
            adv_tot = float(run_query("SELECT COALESCE(SUM(amount),0) as t FROM worker_advances WHERE worker_id=:w AND status='قيد الانتظار'", {"w":wid2})['t'].iloc[0])
            base = st.number_input("الراتب الأساسي:", min_value=0.0, value=5000.0)
            my = st.text_input("الشهر/السنة:", value=datetime.date.today().strftime("%Y-%m"))
            net = base - adv_tot
            st.markdown(f"""<div class="print-card">
            <h4 style="text-align:center;">إيصال راتب - {w_sel2}</h4>
            <p>الأساسي: {base:,.2f} | خصم السلف: -{adv_tot:,.2f} | <b>الصافي: {net:,.2f} ريال</b></p>
            </div>""", unsafe_allow_html=True)
            if st.button("💰 اعتماد الراتب"):
                if run_write("INSERT INTO worker_salaries (worker_id,month_year,base_salary,advances_deducted,net_paid) VALUES (:w,:my,:b,:a,:n)", {"w":wid2,"my":my,"b":base,"a":adv_tot,"n":net}):
                    run_write("UPDATE worker_advances SET status='مخصومة' WHERE worker_id=:w AND status='قيد الانتظار'", {"w":wid2})
                    st.success(f"✅ تم اعتماد راتب {w_sel2}!")

    with tabs[3]:
        s = st.text_input("ابحث باسم العامل أو الإقامة:")
        if s:
            r = run_query("SELECT name,iqama_id,start_date FROM workers WHERE name ILIKE :s OR iqama_id LIKE :s2", {"s":f"%{s}%","s2":f"%{s}%"})
            st.dataframe(r if not r.empty else pd.DataFrame({"النتيجة":["لا توجد نتائج"]}), use_container_width=True)

# ==========================================
# [قسم 7]: الاستعلام المتقدم
# ==========================================
elif menu == "🔍 الاستعلام المتقدم":
    st.subheader("🔍 مركز الاستعلام المتقدم")
    q_type = st.selectbox("نوع الاستعلام:", [
        "عميل — بحث بالاسم أو السجل",
        "طلبية — بحث بالكود أو العميل",
        "مورد — تاريخ المشتريات",
        "خزان — بحث بالرقم المسلسل",
        "فاتورة — بحث برقم الفاتورة"
    ])

    customers_df = run_query("SELECT id, trade_name FROM customers ORDER BY trade_name")
    suppliers_df = run_query("SELECT id, original_name FROM suppliers ORDER BY original_name")
    orders_df = run_query("SELECT order_id FROM orders ORDER BY order_date DESC")

    if q_type == "عميل — بحث بالاسم أو السجل":
        sel = st.selectbox("اختر العميل:", ["الكل"] + (customers_df['trade_name'].tolist() if not customers_df.empty else []))
        if st.button("🔍 بحث"):
            if sel == "الكل":
                df = run_query("SELECT trade_name as الاسم, cr_number as السجل, tax_number as الضريبي FROM customers")
            else:
                df = run_query("SELECT trade_name,cr_number,tax_number FROM customers WHERE trade_name=:n", {"n":sel})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}), use_container_width=True)
            if not df.empty:
                st.download_button("⬇️ تنزيل", df_to_csv(df), "customers.csv", "text/csv")

    elif q_type == "طلبية — بحث بالكود أو العميل":
        sel = st.selectbox("اختر الطلبية:", ["الكل"] + (orders_df['order_id'].tolist() if not orders_df.empty else []))
        if st.button("🔍 بحث"):
            if sel == "الكل":
                df = run_query("SELECT o.order_id,c.trade_name,o.qty,o.total_price,o.status,o.order_date FROM orders o JOIN customers c ON o.customer_id=c.id ORDER BY o.order_date DESC")
            else:
                df = run_query("SELECT o.order_id,c.trade_name,o.qty,o.total_price,o.status,o.order_date FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.order_id=:oid", {"oid":sel})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}), use_container_width=True)
            if not df.empty:
                st.download_button("⬇️ تنزيل", df_to_csv(df), "orders.csv", "text/csv")

    elif q_type == "مورد — تاريخ المشتريات":
        sel = st.selectbox("اختر المورد:", ["الكل"] + (suppliers_df['original_name'].tolist() if not suppliers_df.empty else []))
        if st.button("🔍 بحث"):
            if sel == "الكل":
                df = run_query("SELECT s.original_name,p.date,p.material_name,p.quantity,p.total_price FROM procurement p JOIN suppliers s ON p.supplier_id=s.id ORDER BY p.date DESC")
            else:
                sid = int(suppliers_df[suppliers_df['original_name']==sel]['id'].iloc[0])
                df = run_query("SELECT date,material_name,quantity,unit_price,total_price FROM procurement WHERE supplier_id=:sid ORDER BY date DESC", {"sid":sid})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}), use_container_width=True)
            if not df.empty:
                st.download_button("⬇️ تنزيل", df_to_csv(df), "procurement.csv", "text/csv")

    elif q_type == "خزان — بحث بالرقم المسلسل":
        sn = st.text_input("أدخل الرقم المسلسل أو جزء منه:")
        if st.button("🔍 بحث") and sn:
            df = run_query("SELECT serial_number,order_id,prod_date,supervisor FROM production_tanks WHERE serial_number ILIKE :s", {"s":f"%{sn}%"})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}), use_container_width=True)

    elif q_type == "فاتورة — بحث برقم الفاتورة":
        inv_id = st.number_input("رقم الفاتورة:", min_value=1, value=1)
        if st.button("🔍 بحث"):
            df = run_query("""SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,
                si.grand_total,si.net_required FROM sales_invoices si
                JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id
                WHERE si.invoice_id=:iid""", {"iid":inv_id})
            st.dataframe(df if not df.empty else pd.DataFrame({"النتيجة":["لا يوجد"]}), use_container_width=True)
            if not df.empty:
                st.download_button("⬇️ تنزيل", df_to_csv(df), f"invoice_{inv_id}.csv", "text/csv")

# ==========================================
# [قسم 8]: حذف كامل للبيانات
# ==========================================
elif menu == "🗑️ حذف كامل للبيانات":
    st.subheader("🗑️ حذف كامل لجميع البيانات")
    st.error("⚠️ تحذير: هذه العملية ستحذف جميع البيانات بشكل نهائي ولا يمكن التراجع عنها!")

    confirm = st.radio("هل أنت متأكد من حذف جميع البيانات؟", ["لا، إلغاء العملية", "نعم، أريد الحذف الكامل"])

    if confirm == "نعم، أريد الحذف الكامل":
        st.warning("⚠️ ستُحذف جميع البيانات. اضغط الزر أدناه للتأكيد النهائي.")
        if st.button("🗑️ تأكيد الحذف الكامل — لا رجعة"):
            tables = ["sales_invoices","customer_payments","delivery_orders","production_tanks",
                      "production_days","general_expenses","worker_salaries","worker_advances",
                      "workers","procurement","orders","customers","suppliers"]
            for t in tables:
                run_write(f"DELETE FROM {t}")
            run_write("""UPDATE inventory SET quantity=0.0""")
            st.success("✅ تم حذف جميع البيانات وإعادة ضبط المخزن إلى الصفر.")
            st.balloons()
    else:
        st.info("✅ لم يتم الحذف. العملية ملغاة.")
