import streamlit as st
import pandas as pd
import datetime
import random
from sqlalchemy import text

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
        if qty_f > 0 and uprice_f > 0:
            st.info(f"📊 إجمالي المواد ({qty_f} خزان): راتنج {r_ex*qty_f:.0f} | ألياف {m_ex*qty_f:.0f} | روفرز {v_ex*qty_f:.0f} | تيسو {t_ex*qty_f:.0f} | مصلد {ca_ex*qty_f:.0f} | كالسيوم {cc_ex*qty_f:.0f} | سيليكا {s_ex*qty_f:.0f}")
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
            st.info(f"📋 بيانات الطلبية الحالية: الكمية={int(rr['qty'])} | السعر={float(rr['unit_price']):,.2f} | المقدم={float(rr['advance_paid']):,.2f}")
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
            new_use = e5.selectbox("الاستخدام:", ul, index=ul.index(rr['tank_use']) if rr['tank_use'] in ul else 0, key="eu")
            new_cap = e6.text_input("السعة:", value=str(rr['tank_capacity'] or ""), key="ec")
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
        cdf3 = run_query("SELECT id,trade_name FROM customers ORDER BY trade_name")
        if not cdf3.empty:
            sel_c3 = st.selectbox("اختر العميل:", cdf3['trade_name'].tolist(), key="sc3")
            cid3 = int(cdf3[cdf3['trade_name']==sel_c3]['id'].iloc[0])
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
                    render_header()
                    st.markdown(f"<h2 style='text-align:center;color:#1E3A8A;'>كشف حساب تفصيلي — {sel_c3}</h2>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;'>الفترة: {ds} إلى {de}</p>", unsafe_allow_html=True)
                    st.markdown("---")

                    grand_inv=0.0; grand_paid=0.0; grand_del=0

                    for _, ord_row in orders_stmt.iterrows():
                        oid_s = ord_row['order_id']
                        st.markdown(f"### 📦 طلبية: `{oid_s}`")
                        c1,c2,c3,c4 = st.columns(4)
                        c1.metric("الاستخدام", str(ord_row['tank_use']))
                        c2.metric("السعة", str(ord_row['tank_capacity'] or "—"))
                        c3.metric("النوع", str(ord_row['tank_type']))
                        c4.metric("الحالة", str(ord_row['status']))
                        c5,c6,c7,c8 = st.columns(4)
                        c5.metric("الكمية المطلوبة", f"{int(ord_row['qty'])} خزان")
                        c6.metric("قيمة العقد", f"{float(ord_row['total_price']):,.2f} ر")
                        c7.metric("الدفعة المقدمة", f"{float(ord_row['advance_paid']):,.2f} ر")
                        c8.metric("التاريخ", str(ord_row['order_date']))

                        # التسليمات
                        del_df = run_query("SELECT delivery_id,delivery_date,shipped_qty,driver_name,car_plate FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_date",{"oid":oid_s})
                        total_del = int(del_df['shipped_qty'].sum()) if not del_df.empty else 0
                        rem_tanks = int(ord_row['qty']) - total_del
                        st.write("**🚚 سجل التسليمات:**")
                        if not del_df.empty:
                            st.dataframe(del_df.rename(columns={'delivery_id':'رقم التسليم','delivery_date':'التاريخ','shipped_qty':'الكمية','driver_name':'السائق','car_plate':'اللوحة'}),use_container_width=True)
                        else:
                            st.info("لم يتم تسليم خزانات بعد.")
                        da,db,dc = st.columns(3)
                        da.metric("إجمالي المسلّم", f"{total_del} خزان")
                        db.metric("المتبقي للتسليم", f"{rem_tanks} خزان")
                        pct = int(total_del/int(ord_row['qty'])*100) if int(ord_row['qty'])>0 else 0
                        dc.metric("نسبة الإنجاز", f"{pct}%")

                        # الفواتير
                        inv_s = run_query("SELECT invoice_id,invoice_date,grand_total,advance_deducted,net_required FROM sales_invoices WHERE order_id=:oid ORDER BY invoice_date",{"oid":oid_s})
                        total_inv_ord = float(inv_s['net_required'].sum()) if not inv_s.empty else 0.0
                        st.write("**📄 الفواتير:**")
                        if not inv_s.empty:
                            st.dataframe(inv_s.rename(columns={'invoice_id':'رقم الفاتورة','invoice_date':'التاريخ','grand_total':'الإجمالي','advance_deducted':'المقدم المخصوم','net_required':'المستحق'}),use_container_width=True)
                        else:
                            st.info("لا توجد فواتير.")

                        # الدفعات
                        pay_s = run_query("SELECT payment_date,amount,payment_type,bank_name FROM customer_payments WHERE order_id=:oid AND customer_id=:cid ORDER BY payment_date",{"oid":oid_s,"cid":cid3})
                        total_paid_ord = float(pay_s['amount'].sum()) if not pay_s.empty else 0.0
                        st.write("**💵 الدفعات المستلمة:**")
                        if not pay_s.empty:
                            st.dataframe(pay_s.rename(columns={'payment_date':'التاريخ','amount':'المبلغ','payment_type':'طريقة الدفع','bank_name':'البنك'}),use_container_width=True)
                        else:
                            st.info("لا توجد دفعات.")

                        bal = total_inv_ord - total_paid_ord
                        p1,p2,p3 = st.columns(3)
                        p1.metric("المستحق بالفواتير", f"{total_inv_ord:,.2f} ر")
                        p2.metric("إجمالي المدفوع", f"{total_paid_ord:,.2f} ر")
                        p3.metric("🔴 الرصيد المتبقي", f"{bal:,.2f} ر")
                        grand_inv+=total_inv_ord; grand_paid+=total_paid_ord; grand_del+=total_del
                        st.markdown("---")

                    st.markdown("## 📊 الملخص الإجمالي")
                    g1,g2,g3,g4 = st.columns(4)
                    g1.metric("إجمالي الفواتير", f"{grand_inv:,.2f} ر")
                    g2.metric("إجمالي المدفوع", f"{grand_paid:,.2f} ر")
                    g3.metric("🔴 الرصيد الكلي", f"{grand_inv-grand_paid:,.2f} ر")
                    g4.metric("إجمالي الخزانات المسلمة", f"{grand_del} خزان")
                    summary = pd.DataFrame([{"العميل":sel_c3,"الفترة":f"{ds} إلى {de}","إجمالي الفواتير":grand_inv,"إجمالي المدفوع":grand_paid,"الرصيد":grand_inv-grand_paid,"الخزانات المسلمة":grand_del}])
                    st.download_button("⬇️ تنزيل ملخص كشف الحساب",df_to_csv(summary),f"stmt_{sel_c3}.csv","text/csv")

# ==========================================
# [3] التصنيع
# ==========================================
elif menu == "🏭 التصنيع":
    st.subheader("🏭 إدارة صالة الإنتاج")
    odf = run_query("SELECT o.order_id,c.trade_name,o.qty,o.resin_exp,o.mat_exp,o.roving_exp,o.tissue_exp,o.catalyst_exp,o.calcium_exp,o.silica_exp FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
    if odf.empty:
        st.info("لا توجد طلبيات جارية.")
    else:
        opts = [f"{r['order_id']} | {r['trade_name']} | {r['qty']} خزان" for _,r in odf.iterrows()]
        sel = st.selectbox("اختر الطلبية:", opts)
        oid = sel.split(" | ")[0]
        row = odf[odf['order_id']==oid].iloc[0]
        tanks_today = st.number_input("عدد الخزانات المستهدفة اليوم:", min_value=1, value=2)
        calc = {
            "راتنج": tanks_today*float(row['resin_exp'] or 0),
            "ألياف Mat": tanks_today*float(row['mat_exp'] or 0),
            "روفرز": tanks_today*float(row['roving_exp'] or 0),
            "تيسو": tanks_today*float(row['tissue_exp'] or 0),
            "مصلد": tanks_today*float(row['catalyst_exp'] or 0),
            "كالسيوم": tanks_today*float(row['calcium_exp'] or 0),
            "سيليكا": tanks_today*float(row['silica_exp'] or 0),
        }
        render_header()
        st.markdown(f"<h3 style='text-align:center;'>أمر صرف مواد خام — {oid} — {datetime.date.today()}</h3>", unsafe_allow_html=True)
        disp_df = pd.DataFrame([{"المادة":k,"الكمية":v,"الوحدة":"كجم/م²"} for k,v in calc.items()])
        st.dataframe(disp_df, use_container_width=True)
        st.download_button("⬇️ تنزيل أمر الصرف",df_to_csv(disp_df),f"dispatch_{oid}.csv","text/csv")
        if st.button("🎬 بدء الوردية وخصم المواد"):
            mat_map = {"راتنج كميائي صنف اول للديزل":calc["راتنج"],"ألياف (Mat 450)":calc["ألياف Mat"],"روفرز (Roving 600)":calc["روفرز"],"تيسو (Tissue)":calc["تيسو"],"مصلد (Catalyst)":calc["مصلد"],"كربونات الكالسيوم":calc["كالسيوم"],"سيليكا (Silica)":calc["سيليكا"]}
            for mat,qty in mat_map.items():
                run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name=:m",{"q":qty,"m":mat})
            if run_write("INSERT INTO production_days(order_id,planned_qty,date) VALUES(:oid,:pq,:d)",{"oid":oid,"pq":tanks_today,"d":datetime.date.today()}):
                st.success("✅ تم فتح الوردية وخصم المواد!")
        st.write("---")
        st.markdown("### 🔒 إنهاء الوردية")
        actual_qty = st.number_input("العدد الفعلي:", min_value=0, value=int(tanks_today))
        supervisor = st.text_input("المشرف:")
        if st.button("🔒 إنهاء الوردية"):
            ls = run_query("SELECT id FROM production_days WHERE order_id=:oid ORDER BY id DESC LIMIT 1",{"oid":oid})
            if not ls.empty:
                sid = int(ls['id'].iloc[0])
                run_write("UPDATE production_days SET actual_qty=:aq,status='مغلق' WHERE id=:sid",{"aq":actual_qty,"sid":sid})
                for i in range(1, actual_qty+1):
                    sn = f"SUBUL-SN-{datetime.date.today().year}-{random.randint(10000,99999)}-{i:02d}"
                    run_write("INSERT INTO production_tanks(serial_number,order_id,shift_id,prod_date,supervisor) VALUES(:sn,:oid,:sid,:pd,:sup)",{"sn":sn,"oid":oid,"sid":sid,"pd":datetime.date.today(),"sup":supervisor})
                    st.markdown(f"🔹 خزان {i}: `{sn}`")
                dev = (actual_qty-tanks_today)*float(row['resin_exp'] or 0)
                if dev > 0:
                    run_write("UPDATE inventory SET quantity=quantity-:q WHERE material_name='راتنج كميائي صنف اول للديزل'",{"q":dev})
                    st.warning(f"⚠️ زيادة استهلاك: {dev:.2f} كجم")
                elif dev < 0:
                    run_write("UPDATE inventory SET quantity=quantity+:q WHERE material_name='راتنج كميائي صنف اول للديزل'",{"q":abs(dev)})
                    st.success(f"🟢 وفر: {abs(dev):.2f} كجم أعيدت للمخزن")
                st.success(f"✅ تم إغلاق الوردية — {actual_qty} خزان!")

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

    with tabs[0]:
        odf3 = run_query("SELECT o.order_id,c.trade_name,o.qty,c.cr_number,c.tax_number FROM orders o JOIN customers c ON o.customer_id=c.id WHERE o.status='قيد التنفيذ'")
        if odf3.empty:
            st.info("لا توجد طلبيات.")
        else:
            if 'dok' not in st.session_state: st.session_state.dok = 0
            with st.form(f"dof_{st.session_state.dok}", clear_on_submit=True):
                sel_d = st.selectbox("الطلبية:", [f"{r['order_id']} | {r['trade_name']}" for _,r in odf3.iterrows()])
                oid_d = sel_d.split(" | ")[0]
                or_d = odf3[odf3['order_id']==oid_d].iloc[0]
                shipped = st.number_input("الكمية المشحونة:", min_value=1, value=5)
                dn = st.text_input("السائق:")
                dp = st.text_input("اللوحة:")
                di = st.text_input("الإقامة:")
                if st.form_submit_button("🚀 إصدار أمر التسليم"):
                    if run_write("INSERT INTO delivery_orders(order_id,shipped_qty,driver_name,car_plate,driver_iqama) VALUES(:oid,:sq,:dn,:dp,:di)",{"oid":oid_d,"sq":shipped,"dn":dn,"dp":dp,"di":di}):
                        nd = run_query("SELECT delivery_id FROM delivery_orders WHERE order_id=:oid ORDER BY delivery_id DESC LIMIT 1",{"oid":oid_d})
                        did = int(nd['delivery_id'].iloc[0]) if not nd.empty else "—"
                        qr = f"SUBUL-{random.randint(100000,999999)}"
                        render_header()
                        st.markdown(f"""
                        <div style="border:1px solid #CBD5E1;padding:15px;border-radius:8px;">
                        <h3 style="text-align:center;">أمر تسليم رقم: {did}</h3>
                        <p><b>الطلبية:</b> {oid_d} | <b>العميل:</b> {or_d['trade_name']} | <b>التاريخ:</b> {datetime.date.today()}</p>
                        <p><b>السائق:</b> {dn} | <b>اللوحة:</b> {dp} | <b>الإقامة:</b> {di}</p>
                        <p><b>الكمية:</b> {shipped} خزان</p>
                        <div style="border:2px solid #000;padding:8px;width:180px;margin:10px auto;text-align:center;font-size:12px;">QR: {qr}</div>
                        </div>""", unsafe_allow_html=True)
                        dod = pd.DataFrame([{"أمر التسليم":did,"الطلبية":oid_d,"العميل":or_d['trade_name'],"الكمية":shipped,"السائق":dn,"التاريخ":datetime.date.today()}])
                        st.download_button("⬇️ تنزيل",df_to_csv(dod),f"DO_{did}.csv","text/csv")
                        st.success(f"✅ تم إصدار أمر التسليم #{did}!")
                        st.session_state.dok+=1

    with tabs[1]:
        dldf = run_query("SELECT d.delivery_id,d.order_id,d.shipped_qty,d.delivery_date,o.unit_price,o.advance_paid,o.qty as tq,c.trade_name,c.cr_number,c.tax_number FROM delivery_orders d JOIN orders o ON d.order_id=o.order_id JOIN customers c ON o.customer_id=c.id")
        if dldf.empty:
            st.info("لا توجد أوامر تسليم.")
        else:
            dl_opts = [f"أمر #{r['delivery_id']} | {r['order_id']} | {r['trade_name']} | {r['shipped_qty']} خزان" for _,r in dldf.iterrows()]
            sel_dl = st.selectbox("أمر التسليم:", dl_opts)
            did2 = int(sel_dl.split("#")[1].split(" ")[0])
            dr = dldf[dldf['delivery_id']==did2].iloc[0]
            sub = float(dr['shipped_qty'])*float(dr['unit_price'])
            adv_d = (float(dr['advance_paid'])/float(dr['tq']))*float(dr['shipped_qty']) if float(dr['tq'])>0 else 0
            vat = sub*0.15; grand = sub+vat; net = grand-adv_d
            inv_n = f"INV-{did2}-{datetime.date.today().strftime('%Y%m%d')}"
            render_header()
            st.markdown(f"""
            <div style="border:1px solid #CBD5E1;padding:15px;border-radius:8px;margin-top:10px;">
            <h3 style="text-align:center;color:#1E3A8A;">فاتورة ضريبية رسمية | {inv_n}</h3>
            <p><b>التاريخ:</b> {datetime.date.today()} | <b>العميل:</b> {dr['trade_name']} | <b>س.ت:</b> {dr['cr_number']} | <b>الرقم الضريبي:</b> {dr['tax_number']}</p>
            <table style="width:100%;border-collapse:collapse;" border="1">
            <tr style="background:#1E3A8A;color:white;"><th style="padding:5px;">البيان</th><th>الكمية</th><th>سعر الوحدة</th><th>الإجمالي</th></tr>
            <tr><td style="padding:5px;">خزانات فايبر جلاس</td><td>{dr['shipped_qty']}</td><td>{float(dr['unit_price']):,.2f}</td><td>{sub:,.2f}</td></tr>
            </table>
            <p style="margin-top:10px;">قبل الضريبة: {sub:,.2f} ر | ضريبة 15%: {vat:,.2f} ر | الإجمالي: {grand:,.2f} ر</p>
            <p style="color:green;">خصم المقدم: -{adv_d:,.2f} ر</p>
            <h3 style="color:red;">الصافي المستحق: {net:,.2f} ريال</h3>
            </div>""", unsafe_allow_html=True)
            idl = pd.DataFrame([{"رقم الفاتورة":inv_n,"العميل":dr['trade_name'],"الإجمالي":grand,"الصافي":net,"التاريخ":datetime.date.today()}])
            st.download_button("⬇️ تنزيل الفاتورة",df_to_csv(idl),f"{inv_n}.csv","text/csv")
            if st.button("💾 حفظ الفاتورة"):
                if run_write("INSERT INTO sales_invoices(delivery_id,order_id,subtotal,vat,grand_total,advance_deducted,net_required) VALUES(:did,:oid,:st,:v,:gt,:ad,:nr)",{"did":did2,"oid":dr['order_id'],"st":sub,"v":vat,"gt":grand,"ad":adv_d,"nr":net}):
                    st.success(f"✅ تم حفظ الفاتورة {inv_n}!")

    with tabs[2]:
        if 'rk' not in st.session_state: st.session_state.rk = 0
        cdf4 = run_query("SELECT id,trade_name FROM customers")
        if not cdf4.empty:
            with st.form(f"rf_{st.session_state.rk}", clear_on_submit=True):
                sc4 = st.selectbox("العميل:", cdf4['trade_name'].tolist())
                cid4 = int(cdf4[cdf4['trade_name']==sc4]['id'].iloc[0])
                odf4 = run_query("SELECT order_id FROM orders WHERE customer_id=:c",{"c":cid4})
                so4 = st.selectbox("الطلبية:", odf4['order_id'].tolist() if not odf4.empty else ["—"])
                pa4 = st.number_input("المبلغ:", min_value=0.0, value=0.0)
                pt4 = st.selectbox("طريقة الدفع:", ["نقدي","تحويل بنكي","شبكة مدى"])
                pb4 = st.text_input("البنك:")
                if st.form_submit_button("💵 اعتماد"):
                    if run_write("INSERT INTO customer_payments(customer_id,order_id,amount,payment_type,bank_name) VALUES(:ci,:oi,:a,:pt,:b)",{"ci":cid4,"oi":so4,"a":pa4,"pt":pt4,"b":pb4}):
                        st.success(f"✅ تم تسجيل {pa4:,.2f} ريال!")
                        st.session_state.rk+=1; st.rerun()

    with tabs[3]:
        cdf5 = run_query("SELECT id,trade_name FROM customers")
        if not cdf5.empty:
            sc5 = st.selectbox("العميل:", ["الكل"]+cdf5['trade_name'].tolist(), key="iq")
            d1,d2 = st.columns(2)
            ds5 = d1.date_input("من:", datetime.date.today()-datetime.timedelta(days=90), key="ids")
            de5 = d2.date_input("إلى:", datetime.date.today(), key="ide")
            if st.button("🔍 بحث"):
                if sc5=="الكل":
                    ir = run_query("SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,si.grand_total,si.net_required FROM sales_invoices si JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id WHERE si.invoice_date BETWEEN :s AND :e ORDER BY si.invoice_date DESC",{"s":ds5,"e":de5})
                else:
                    ci5 = int(cdf5[cdf5['trade_name']==sc5]['id'].iloc[0])
                    ir = run_query("SELECT si.invoice_id,si.invoice_date,o.order_id,c.trade_name,si.grand_total,si.net_required FROM sales_invoices si JOIN orders o ON si.order_id=o.order_id JOIN customers c ON o.customer_id=c.id WHERE o.customer_id=:cid AND si.invoice_date BETWEEN :s AND :e ORDER BY si.invoice_date DESC",{"cid":ci5,"s":ds5,"e":de5})
                st.dataframe(ir if not ir.empty else pd.DataFrame({"الحالة":["لا توجد"]}),use_container_width=True)
                if not ir.empty: st.download_button("⬇️ تنزيل",df_to_csv(ir),"invoices.csv","text/csv")

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
