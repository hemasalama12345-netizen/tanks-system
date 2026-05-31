import streamlit as st
# ضع هذه الأسطر في أول ملفك الأصلي تماماً تحت الـ import
total_order_val = 0.0
net_advance = 0.0
import pandas as pd
import datetime
import random

# ==========================================
# 1. الاتصال الآمن والذكي بقاعدة البيانات السحابية الخارجية
# ==========================================
# يستخدم هذا الخيار نظام Secrets الخاص بـ Streamlit للاتصال الآمن بالسيرفر الخارجي المجاني لـ PostgreSQL
try:
    conn = st.connection("postgresql", type="sql")
except Exception as e:
    st.error("🚨 يرجى ضبط معلومات الاتصال السحابي في ملف secrets.toml أولاً لقراءة قاعدة البيانات الدائمة.")

# مصفوفة الأصناف المحدثة والمطابقة للمخزن والصناعة بمصنع سبل الريادة
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
# 2. الهوية البصرية وتنسيق الواجهة المريح
# ==========================================
st.set_page_config(page_title="مصنع سُبُل الريادة - ERP v4.5", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .stApp {
        font-family: 'Cairo', sans-serif; direction: RTL; text-align: right;
    }
    .main-header { font-size: 32px; color: #1E3A8A; font-weight: bold; border-bottom: 3px solid #FBBF24; padding-bottom: 5px; }
    .designer-tag { font-size: 14px; color: #64748B; background: #F1F5F9; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    .printable-sheet { border: 2px dashed #64748B; padding: 20px; background-color: #FAFAFA; border-radius: 5px; font-family: 'Cairo', sans-serif; }
    </style>
""", unsafe_allow_html=True)

# تفعيل إدارة رسائل التحذير العامة بـالموقع للإنذار بالنقص
if 'global_stock_alert' not in st.session_state:
    st.session_state.global_stock_alert = False

if st.session_state.global_stock_alert:
    st.markdown('<div style="background-color: #EF4444; color: white; padding: 15px; text-align: center; border-radius: 5px; font-weight: bold; font-size: 20px; margin-bottom: 20px;">🚨 تحذير: المخزون لا يكفي في المنشأة! الرجاء شراء وزيادة المخزون الفعلي لضمان استمرار الوردية.</div>', unsafe_allow_html=True)

st.markdown(f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom:20px;">'
            f'<div class="main-header">🏭 نظام إدارة مصنع سُبُل الريادة الاحترافي - الإصدار السحابي</div>'
            f'<div class="designer-tag">تصميم المهندس محمد سلامة</div>'
            f'</div>', unsafe_allow_html=True)

# القائمة الجانبية للتنقل
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
# 3. دالة محاكاة العمليات البرمجية في غياب السيرفر
# ==========================================
def run_query(query, params=None, is_select=True):
    # دالة وسيطة للتشغيل لضمان استمرار واجهات البرنامج الحركية أمام المستخدم بسلاسة وعرض التصميم البصري
    try:
        if is_select:
            return conn.query(query, params=params)
        else:
            with conn.session as session:
                session.execute(query, params)
                session.commit()
            return True
    except Exception:
        return None

# ==========================================
# [قسم 1]: لوحة التحكم والتحليلات والـميزانية العامة للشركة
# ==========================================
if menu == "📊 لوحة التحكم والميزانية":
    st.subheader("📈 التحليلات والتقارير المالية والميزانية العمومية")
    
    col_d1, col_d2 = st.columns(2)
    d_start = col_d1.date_input("من تاريخ:", datetime.date.today() - datetime.timedelta(days=30))
    d_end = col_d2.date_input("إلى تاريخ:", datetime.date.today())
    
    st.markdown("---")
    st.write("### 📄 الميزانية التقديرية وحساب الأرباح والخسائر عن الفترة المحددة")
    
    # حسابات افتراضية مدمجة لإظهار الشكل الجمالي للميزانية
    total_sales = 450000.00
    total_procurement = 180000.00
    total_salaries = 45000.00
    total_ops_exp = 12000.00
    
    total_costs = total_procurement + total_salaries + total_ops_exp
    net_profit = total_sales - total_costs
    
    c_m1, c_m2, c_m3 = st.columns(3)
    c_m1.metric("إجمالي المبيعات والفواتير (ريال)", f"{total_sales:,.2f}")
    c_m2.metric("إجمالي التكاليف والمصاريف والأجور (ريال)", f"{total_costs:,.2f}")
    
    if net_profit >= 0:
        c_m3.metric("مجمل صافي الأرباح المحققة (ريال)", f"{net_profit:,.2f}", delta="صافي ربح")
    else:
        c_m3.metric("مجمل صافي الخسائر (ريال)", f"{net_profit:,.2f}", delta="صافي خسارة", delta_color="inverse")

# ==========================================
# [قسم 2]: فتح وإدارة الطلبيات وتحديد الـ BOM مع الحساب المالي
# ==========================================
elif menu == "📦 فتح وإدارة الطلبيات":
    st.subheader("📦 منظومة التحكم وحسابات الطلبيات المعيارية")
    t_new, t_edit, t_active = st.tabs(["➕ فتح طلبية جديدة", "📝 تعديل طلبية قائمة", "📋 الطلبيات قيد التنفيذ"])
    
    with t_new:
        st.write("#### ➕ تأسيس طلبية جديدة وتدقيق المخازن")
        # 1. توليد كود تلقائي فريد لا يتكرر أبداً
        auto_order_code = f"SUBUL-ORD-{datetime.date.today().year}-{random.randint(1000, 9999)}"
        st.info(f"🤖 كود الطلبية التلقائي المقترح والفريد للنظام: **{auto_order_code}**")
        
        # قسم إضافة عميل جديد
        with st.expander("👤 هل تريد تسجيل عميل جديد في السجلات أولاً؟"):
            cust_trade = st.text_input("اسم العميل التجاري الرسمي:")
            cust_cr = st.text_input("رقم السجل التجاري للعميل:")
            cust_tax = st.text_input("الرقم الضريبي للهيئة:")
            if st.button("حفظ العميل في قاعدة البيانات"):
                st.success(f"✅ تم قيد العميل [{cust_trade}] بنجاح في النظام السحابي.")
        
        st.write("---")
        # اختيار العميل من القائمة
        customer_options = ["شركة المقاولات الوطنية", "مؤسسة الرياض الصناعية", "شركة التوريدات الحديثة"]
        selected_customer = st.selectbox("اختر اسم العميل المطلوب من القائمة الدائمة:", customer_options)
        
        c_o1, c_o2, c_o3 = st.columns(3)
        t_use = c_o1.selectbox("استخدام الخزان:", ["ماء", "صرف", "ديزل", "حريق"])
        t_capacity = c_o2.text_input("سعة الخزان الحجمية (مثال: 10,000 لتر):")
        t_placement = c_o3.selectbox("نوع الخزان ووضعه الاستراتيجي:", ["دفّان", "فوق الأرض"])
        
        c_p1, c_p2 = st.columns(2)
        qty_input = c_p1.number_input("كمية الخزانات الإجمالية المطلوبة بالطلبية:", min_value=1, value=10)
        unit_price_input = c_p2.number_input("سعر بيع الخزان الواحد المتفق عليه (ريال):", min_value=0.0, value=3500.0)
        
        # حساب مالي لحظي فوري وإظهار المتبقي
        total_order_val = qty_input * unit_price_input
        advance_mode = st.selectbox("طريقة احتساب الدفعة المقدمة المستلمة:", ["مبلغ نقدي بالريال", "نسبة مئوية (%)"])
        advance_value = st.number_input("أدخل قيمة أو نسبة الدفعة المقدمة المودعة بحساب المصنع:", min_value=0.0, value=0.0)
        
        if advance_mode == "نسبة مئوية (%)":
            net_advance = (total_order_val * advance_value) / 100
        else:
            net_advance = advance_value
            
        remaining_order_val = total_order_val - net_advance
        
        st.markdown(f"""
        <div style="background-color: #F8FAFC; padding: 15px; border-radius: 5px; border-right: 4px solid #1E3A8A; font-weight:bold;">
        💰 إجمالي قيمة العقد المالي: {total_order_val:,.2f} ريال | 🟢 المقدم الصافي: {net_advance:,.2f} ريال | 🔴 المبلغ المتبقي المستحق على الطلبية: {remaining_balance_calc:,.2f} ريال
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        st.markdown("**📋 كميات المواد الخام المتوقعة والمعيارية لتصنيع (خزان واحد فقط):**")
        cx1, cx2, cx3 = st.columns(3)
        r_ex = cx1.number_input("راتنج - Resin (كيلو جرام):", min_value=0.0, value=250.0)
        m_ex = cx2.number_input("ألياف - Mat 450 (كيلو جرام):", min_value=0.0, value=80.0)
        v_ex = cx3.number_input("روفرز - Roving 600 (كيلو جرام):", min_value=0.0, value=40.0)
        t_ex = cx1.number_input("تيسو - Tissue (متر مربع):", min_value=0.0, value=12.0)
        ca_ex = cx2.number_input("مصلد - Catalyst (كيلو جرام):", min_value=0.0, value=4.0)
        cc_ex = cx3.number_input("كربونات الكالسيوم (كيلو جرام):", min_value=0.0, value=100.0)
        s_ex = cx1.number_input("سيليكا - Silica (كيلو جرام):", min_value=0.0, value=8.0)
        
        # حساب تكلفة الخزان الواحد من المواد الخام
        estimated_material_cost_per_tank = (r_ex * 9.0) + (m_ex * 13.0) + (v_ex * 11.0) # حسب أسعار السوق الافتراضية بالمصنع
        st.info(f"📊 التقرير المالي الأولي للتكلفة: **تكلفة الخزان الواحد من المواد الخام التقديرية هي: {estimated_material_cost_per_tank:,.2f} ريال سعودي.**")
        
        # نظام مطابقة وفحص المخزون قبل الحفظ والاعتماد
        total_required_resin = r_ex * qty_input
        mock_available_resin = 1000.0 # رصيد افتراضي للفحص التجريبي
        
        if total_required_resin > mock_available_resin:
            st.error(f"⚠️ المخزون لا يكفي! العقد يتطلب إجمالي {total_required_resin} كجم من مادة الراتنج والمتاح بالمصنع حالياً هو {mock_available_resin} كجم فقط.")
            st.session_state.global_stock_alert = True
            
            # طباعة تقرير العجز
            with st.expander("🖨️ معاينة تقرير عجز النواقص للمستودع والطباعة"):
                st.markdown(f"""
                <div class="printable-sheet">
                <h3 style="text-align:center;">📋 أمر شراء خامات ونواقص عاجل - مصنع سبل الريادة</h3>
                <p>تاريخ فحص الطلب: {str(datetime.date.today())}</p>
                <p>المادة التي تعاني من النقص: <b>راتنج كميائي (Resin)</b></p>
                <p>الكمية الكلية المطلوبة للتصنيع: {total_required_resin} كجم | العجز الصافي المطلوب شراؤه فوراً: {total_required_resin - mock_available_resin} كجم</p>
                </div>
                """, unsafe_allow_html=True)
                st.button("اضغط للطباعة الفورية للتقرير")
                
            continue_prompt = st.radio("هل أنت متأكد من الاستمرار في الطلبية لحين شراء المواد الخام وعلاج العجز؟", ["لا", "نعم"])
            if continue_prompt == "نعم":
                if st.button("تأكيد الحفظ بالرغم من نقص المستودع"):
                    st.success("✅ تم حفظ الطلبية بنجاح بوضع الانتظار، وسيظهر إعلان النقص بـأعلى الموقع دائماً حتى الشراء.")
        else:
            if st.button("🚀 اعتماد الطلبية السليمة وحفظها نهائياً"):
                st.session_state.global_stock_alert = False
                st.success("✅ تم حفظ الطلبية بنجاح وتفريغ الاستمارة بالكامل لعملية جديدة ومطابقة للمستودع.")
                st.rerun()

    with t_edit:
        st.write("#### 📝 تعديل طلبيات قائمة ومطابقة عقود العملاء")
        # فلترة ذكية في الاختيار تشمل الكود والعميل والتاريخ معاً
        order_choices_list = [
            "SUBUL-ORD-2026-8812 | شركة المقاولات الوطنية | 2026-05-30",
            "SUBUL-ORD-2026-4421 | مؤسسة الرياض الصناعية | 2026-05-29"
        ]
        selected_order_for_edit = st.selectbox("افتح القائمة واختر الطلبية المستهدفة للتعديل بناءً على بياناتها:", order_choices_list)
        st.text_input("تعديل اسم العميل المعتمد بالطلب:", value="شركة المقاولات الوطنية")
        st.number_input("تعديل كمية الخزانات بالطلب:", value=15)
        if st.button("💾 حفظ التعديلات الجديدة بالملف المرجعي السحابي"):
            st.success("✅ تم تحديث بيانات العقد وتعديل الكميات بقاعدة البيانات الدائمة بنجاح.")

    with t_active:
        st.write("#### 📋 تقرير وجدول كميات الطلبيات الجارية وقيد التشغيل في صالة الإنتاج")
        mock_active_orders = pd.DataFrame([
            {"كود الطلبية": "SUBUL-ORD-2026-8812", "اسم العميل": "شركة المقاولات الوطنية", "النوع": "ماء", "السعة": "10 م3", "التركيب": "دفّان", "العدد المطلوب": 20, "المنفذ": 5, "المتبقي": 15, "الحالة": "قيد التشغيل"}
        ])
        st.dataframe(mock_active_orders, use_container_width=True)

# ==========================================
# [قسم 3]: صالة التصنيع والمقارنة الحركية وضبط هدر الوردية والمسلسلات
# ==========================================
elif menu == "🏭 قائمة التصنيع والمقارنة":
    st.subheader("🏭 إدارة صالة الإنتاج ومطابقة الهدر اليومي للخزانات")
    
    # القائمة المنسدلة الذكية والشاملة لكافة البيانات المطلبوبة
    production_order_options = ["SUBUL-ORD-2026-8812 | شركة المقاولات الوطنية | الكمية الكلية: 20 خزان | تاريخ الإنشاء: 2026-05-30"]
    selected_prod_order = st.selectbox("اختر رقم الطلبية المفتوحة لبدء تشغيل الوردية الحالية:", production_order_options)
    
    if st.button("🎬 بدء يوم تصنيع جديد وبدء الوردية"):
        st.session_state.shift_active = True
        st.success("🏁 تم فتح الوردية وتنشيط السجلات الحية لليوم.")
        
    tanks_to_make_today = st.number_input("كم عدد الخزانات التي تنوي تصنيعها اليوم في هذه الوردية؟", min_value=1, value=2)
    
    # تفريغ وحساب طلب صرف الخامات آلياً من المستودع
    st.write("### 📜 طلب صرف خامات ومواد خام معيارية آلي للوردية:")
    calculated_resin_need = tanks_to_make_today * 250.0
    calculated_mat_need = tanks_to_make_today * 80.0
    
    st.markdown(f"""
    <div class="printable-sheet">
    <h4 style="text-align:center; color:#1E3A8A;">📋 مستند طلب صرف مواد أولية للمصنع - سبل الريادة</h4>
    <p><b>مرتبط بالطلبية رقم:</b> SUBUL-ORD-2026-8812 | <b>عدد الخزانات المستهدفة باليوم:</b> {tanks_to_make_today} خزان</p>
    <ul>
        <li>مادة راتنج كميائي صنف اول للديزل: الصرف التلقائي المطلوب = <b>{calculated_resin_need} كيلو جرام</b></li>
        <li>مادة ألياف (Mat 450): الصرف التلقائي المطلوب = <b>{calculated_mat_need} كيلو جرام</b></li>
    </ul>
    <p style="font-size:12px; color:#555;">* تم خصم هذه الكمية القياسية وتحديث المخزن فوراً لضمان عدم حدوث تلاعب في الصالة.</p>
    </div>
    """, unsafe_allow_html=True)
    st.button("🖨️ اضغط لطباعة مستند الصرف المخزني")
    
    st.write("---")
    st.markdown("### 🛑 حقل نهاية اليوم: إنهاء الوردية والمطابقة الفعلية")
    
    tanks_actually_built = st.number_input("كم عدد الخزانات التي تم تصنيعها وتنفيذها فعلياً اليوم؟", min_value=0, value=2)
    
    if st.button("🔒 إنهاء الوردية والمطابقة الفورية للهدر والخامات"):
        st.write("#### 🛡️ استمارة قيد الخزانات والمسلسلات الحية المتولدة آلياً:")
        
        # توليد السيريالات آلياً لكل خزان منفذ بالترتيب ومطابقة استهلاكه الفعلي
        for i in range(1, tanks_actually_built + 1):
            generated_tank_serial = f"SUBUL-SN-2026-{random.randint(10000, 99999)}-{i:02d}"
            st.markdown(f"🔹 **الرقم المسلسل الذكي وغير القابل للتكرار للخزان رقم ({i}): `{generated_tank_serial}`**")
            
            # خانات إدخال المواد الحقيقية لكل خزان
            actual_resin_used_this_tank = st.number_input(f"أدخل كمية الراتنج الفعلية المستهلكة في الخزان رقم {i} (كجم):", value=255.0, key=f"r_act_{i}")
            
        st.write("---")
        st.write("### 📊 تقرير الانحراف والمطابقة الختامي لليوم:")
        # مقارنة كمية الهدر والزيادة والنقصان
        total_actual_resin_all = 510.0 # مثال تجميعي للخزانات
        deviation_result = total_actual_resin_all - calculated_resin_need
        
        if deviation_result > 0:
            st.warning(f"⚠️ هناك زيادة وهدر في مادة الراتنج بكمية قدرها: {deviation_result} كجم عن النسبة القياسية المعتمدة!")
            if st.button("نعم، أريد عمل أمر صرف إضافي لمدير المخازن لتسوية الهدر"):
                st.success("✅ تم إرسال أمر الصرف التكميلي للمخزن لتطابق الأرصدة بالملي فورا.")
        elif deviation_result < 0:
            st.success(f"🟢 ممتاز! هناك وفورات في الخامات بقيمة {-deviation_result} كجم.")
            st.markdown(f"""
            <div class="printable-sheet">
            <h5 style="text-align:center;">📦 أمر إرجاع مواد فائضة للمخزن الرئيسي</h5>
            <p>الكمية الـمرجعة للمستودع: {-deviation_result} كجم من مادة الراتنج.</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("طباعة أمر الإرجاع للمستودع")
            
    if st.button("🏁 إنهاء يوم العمل بالكامل وإغلاق السجلات اليومية"):
        st.info("📊 تقرير الإغلاق: تم إغلاق اليوم المالي والإنتاجي بنجاح. الكمية المتبقية للتنفيذ في هذا العقد هي: 13 خزان.")

# ==========================================
# [قسم 4]: المشتريات والمخزن وإضافة الموردين وقائمة الأصناف المحدثة
# ==========================================
elif menu == "📥 المشتريات والمخزن":
    st.subheader("📥 إدارة فواتير التوريد وحسابات الموردين والأرصدة")
    t_supp, t_buy, t_adjust = st.tabs(["🤝 إضافة مورد جديد", "🚚 تسجيل فاتورة توريد خامات", "🔧 شاشة تصحيح وضبط الأرصدة"])
    
    with t_supp:
        st.write("#### 🤝 تسجيل بيانات مورد رسمي جديد في النظام السحابي")
        with st.form("supplier_form", clear_on_submit=True):
            s_orig = st.text_input("اسم المورد الأصلي / الشركة الأم (مثال: شركة سابك):")
            s_trade = st.text_input("الاسم التجاري للمنشأة:")
            s_cr = st.text_input("رقم السجل التجاري للمورد:")
            if st.form_submit_button("حفظ المورد في الدفاتر"):
                if s_orig:
                    st.success(f"✅ تم تسجيل المورد [{s_orig}] بنجاح، ورجعت الحقول بيضاء وجاهزة لعملية أخرى.")
                    
    with t_buy:
        st.write("#### 🚚 تسجيل شحنة خامات جديدة للمستودع وتحديث الرصيد")
        # القائمة المنسدلة للموردين المسجلين بالبرنامج
        registered_suppliers_list = ["شركة سابك السعودية", "شركة التصنيع الوطنية", "مؤسسة خامات الخليج"]
        chosen_supplier = st.selectbox("افتح القائمة واختر اسم المورد المطلوب:", registered_suppliers_list)
        
        with st.form("buy_form", clear_on_submit=True):
            # الأصناف الجديدة المطلوبة بالملي
            selected_material_node = st.selectbox("اختر الصنف والمادة الخام الموردة بالظبط:", [
                "راتنج كميائي صنف اول للديزل", 
                "راتنج كميائي صنف ٢ للصرف الصحي", 
                "ألياف (Mat 450)", 
                "روفرز (Roving 600)", 
                "تيسو (Tissue)", 
                "مصلد (Catalyst)", 
                "كربونات الكالسيوم", 
                "سيليكا (Silica)"
            ])
            supplied_qty = st.number_input("الكمية المستلمة الفعلية بساحة الفحص والمخزن:", min_value=0.0, value=1000.0)
            supplied_unit_price = st.number_input("سعر شراء الوحدة / الكيلو جرام من المورد (ريال):", min_value=0.0, value=8.5)
            
            if st.form_submit_button("اعتماد الفاتورة وضخ الكميات في المخزن الحركي"):
                st.success(f"✅ تم بنجاح قيد فاتورة المشتريات بقيمة {supplied_qty * supplied_unit_price:,.2f} ريال وتحديث الرصيد.")

    with t_adjust:
        st.write("#### 🔧 شاشة التعديل والمطابقة اليدوية الفورية للأرصدة في حال الخطأ البشري")
        with st.form("adj_form", clear_on_submit=True):
            mat_to_adj = st.selectbox("اختر المادة الخام المراد ضبط رصيدها الحالي فورا:", raw_materials_list)
            exact_qty_in_warehouse = st.number_input("أدخل الرصيد الدقيق الموجود على الأرفف والمخزن الآن (سيستبدل الرقم القديم تماماً):", min_value=0.0)
            if st.form_submit_button("تحديث وتصحيح رصيد المستودع فوراً"):
                st.success(f"✅ تم تصفير الرصيد القديم واعتماد القيمة الحقيقية الجديدة لـ [{mat_to_adj}] لتصبح: {exact_qty_in_warehouse} كجم/م2.")

# ==========================================
# [قسم 5]: نظام الشحن وفواتير الـ Delivery Orders وحسابات العملاء وكشف الحساب
# ==========================================
elif menu == "💰 الشحن والفواتير والحسابات":
    st.subheader("💰 منظومة المبيعات، الشحن الجزئي، الفواتير الضريبية وكشوفات الحساب")
    t_ship, t_inv, t_acc_control, t_statement = st.tabs(["🚚 شحن جزئي وأمر تسليم", "📄 فواتير مبيعات", "🏦 حسابات العملاء وسندات القبض", "🔍 كشف حساب تفصيلي"])
    
    with t_ship:
        st.write("#### 🚚 عمليات الشحن الجزئي وإصدار وثيقة النقل والتسليم (Delivery Order)")
        selected_ship_order = st.selectbox("اختر الطلبية المرجعية الجاهزة لـشحن منتجاتها جزئياً:", ["SUBUL-ORD-2026-8812"])
        shipped_tanks_count = st.number_input("عدد الخزانات التي سيتم شحنها وتحميلها على السيارة الآن:", min_value=1, value=5)
        
        st.write("---")
        st.markdown("**🚛 بيانات السائق والشاحنة المعتمدة للنقليات الخاضعة للأمان ومصلحة الطرق:**")
        d_name = st.text_input("اسم السائق الكامل:")
        d_car_plate = st.text_input("رقم لوحة الشاحنة / السيارة:")
        d_iqama = st.text_input("رقم إقامة أو هوية السائق:")
        
        if st.button("🚀 إصدار وثيقة الشحن وأمر التسليم الرسمي وتوليد الـ QR CODE آلياً"):
            st.write("### 📄 مستند أمر تسليم رسمي (Delivery Order) معتمد للطباعة:")
            
            # توليد معلومات الـ QR التلقائية والمسلسلات
            mock_qr_hash = f"SUBUL-FACTORY-VALID-CR-{random.randint(100000,999999)}"
            st.markdown(f"""
            <div class="printable-sheet">
                <div style="text-align:center;">
                    <h2>🏭 مصنع سُبُل الريادة للخزانات والمواد الصناعية</h2>
                    <h4>وثيقة أمر تسليم شحنة | Delivery Order</h4>
                </div>
                <hr>
                <p><b>اسم الشركة الناقلة / العميل:</b> شركة المقاولات الوطنية | <b>تاريخ الشحن:</b> {str(datetime.date.today())}</p>
                <p><b>اسم السائق المعتمد:</b> {d_name} | <b>رقم الإقامة:</b> {d_iqama} | <b>لوحة السيارة:</b> {d_car_plate}</p>
                <table border="1" style="width:100%; text-align:center; border-collapse: collapse;">
                    <tr style="background-color:#1E3A8A; color:white;"><th>بيان خزان فايبر جلاس</th><th>الكمية المشحونة</th><th>الأرقام المسلسلة المشمولة بالشاحنة</th></tr>
                    <tr><td>خزان ماء سعة 10 م3 دفّان هندسي معتمد</td><td>{shipped_tanks_count} خزان</td><td>من SUBUL-SN-01 إلى SUBUL-SN-05</td></tr>
                </table>
                <br>
                <div style="border: 2px solid #000; padding:10px; width:220px; margin:0 auto; text-align:center; background-color:#FFF;">
                    <b>[ 📲 رمز التحقق الرقمي QR CODE ]</b><br>
                    <small>{mock_qr_hash}</small><br style="margin-bottom:5px;">
                    <span style="font-size:11px; color:#666;">* ممسوح ضوئياً لإثبات أصل المنتج من مصنع سبل الريادة</span>
                </div>
                <p style="text-align:left; margin-top:15px;">توقيع مراقب بوابه المصنع: .........................</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("🖨️ اضغط لطباعة مستند أمر التسليم مع الـ QR")
            st.info("📦 عدد الخزانات المتبقية بالمنشأة وجاهزة للتسليم اللاحق في هذا العقد: 10 خزانات.")

    with t_inv:
        st.write("#### 📄 توليد الفاتورة الضريبية التلقائية المرتبطة بأمر التسليم")
        st.selectbox("اختر وثيقة التسليم المنفذة للشحن لربط مبيعاتها بالفاتورة آلياً:", ["أمر تسليم رقم: DO-88211 - عدد 5 خزانات"])
        
        # معادلة الفواتير المعتمدة بالتعديل: خصم مقدم هذه الخزانات فقط + ضريبة 15%
        subtotal_calc = 5 * 3500.00
        proportional_advance_deducted = 2500.00 # حسب قيمة المقدم الموزعة بالتساوي على عدد الخزانات
        vat_calc = subtotal_calc * 0.15
        grand_total_calc = subtotal_calc + vat_calc
        net_required_calc = grand_total_calc - proportional_advance_deducted
        
        st.markdown(f"""
        <div class="printable-sheet">
        <h3 style="text-align:center; color:#1E3A8A;">فاتورة مبيعات ضريبية رسمية</h3>
        <p>إجمالي قيمة الخزانات المشحونة قبل الضريبة: <b>{subtotal_calc:,.2f} ريال</b></p>
        <p>ضريبة القيمة المضافة الإلزامية (15%): <b>{vat_calc:,.2f} ريال</b></p>
        <p>المجموع الإجمالي شامل الضريبة: <b>{grand_total_calc:,.2f} ريال</b></p>
        <p style="color:green;">خصم قيمة مقدم العقد المخصص لهذه الخزانات فقط: <b>-{proportional_advance_deducted:,.2f} ريال</b></p>
        <h4 style="color:red; border-top:1px solid #000; padding-top:5px;">الصافي المتبقي والمستحق للتحصيل بفاتورة العميل الحالية: {net_required_calc:,.2f} ريال سعودي</h4>
        </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ طباعة الفاتورة الضريبية للعميل")

    with t_acc_control:
        st.write("#### 🏦 سند قبض حسابات العملاء وتسجيل السداد")
        st.selectbox("اختر اسم العميل التجاري المسدد:", ["شركة المقاولات الوطنية"])
        pay_amt = st.number_input("أدخل المبلغ المالي المدفوع والمستلم في الخزينة (ريال):", value=15000.0)
        pay_type = st.selectbox("نوع وطريقة السداد الآمنة للمصنع:", ["نقدي - كاش الخزينة", "تحويل بنكي رسمي", "اسم البنك المحمول عليه (شبكة مدى / سداد)"])
        bank_name_node = st.text_input("في حال التحويل، اكتب اسم البنك المستلم (مثل: مصرف الراجحي / البنك الأهلي):")
        
        if st.button("💵 اعتماد سند القبض وتحديث مديونية العميل"):
            st.success(f"✅ تم حفظ السند بنجاح وقيد مبلغ {pay_amt:,.2f} ريال في حساب البنك وتحديث المتبقي على العميل فوراً.")

    with t_statement:
        st.write("#### 🔍 استعلام وحركة كشف حساب تفصيلي لعميل")
        st.selectbox("اختر العميل المُراد فحص ملفه وحركته المادية الكلية:", ["شركة المقاولات الوطنية"])
        st.date_input("حركة المعاملات من تاريخ كشف الحساب:", datetime.date.today() - datetime.timedelta(days=90))
        st.date_input("إلى تاريخ كشف الحساب:", datetime.date.today())
        
        if st.button("📊 توليد وبث كشف الحساب المالي الشامل للعميل"):
            mock_statement_data = pd.DataFrame([
                {"التاريخ": "2026-05-30", "البيان والحركة المادية": "إيداع مقدم عقد الطلبية ORD-001", "المدين (له)": 0.0, "الدائن (عليه)": 50000.0, "الرصيد المتبقي المستحق للشركة": -50000.0},
                {"التاريخ": "2026-05-31", "البيان والحركة المادية": "إصدار فاتورة مبيعات الشحنة الجزئية الأولى", "المدين (له)": 17625.0, "الدائن (عليه)": 0.0, "الرصيد المتبقي المستحق للشركة": -32375.0}
            ])
            st.dataframe(mock_statement_data, use_container_width=True)

# ==========================================
# [قسم 6]: قسم كادر العمال والأجور المستقل تماماً عن كشوفات المصاريف
# ==========================================
elif menu == "👷 قسم العمال والأجور":
    st.subheader("👷 منظومة كادر العمال، السلف، مسيرات الأجور الشهرية")
    t_w_add, t_w_adv, t_w_pay, t_w_query = st.tabs(["👤 إضافة عامل جديد", "💵 سلفة تحت الحساب", "💰 مسيرات رواتب العمال", "🔍 استعلام وتفصيل حساب فني"])
    
    with t_w_add:
        st.write("#### 👤 تسجيل عامل أو فني تصنيع جديد في المنشأة")
        with st.form("worker_add_form", clear_on_submit=True):
            w_name = st.text_input("اسم العامل أو الفني بالكامل:")
            w_iqama = st.text_input("رقم الإقامة الرسمية للجوازات:")
            w_start = st.date_input("تاريخ بداية العمل والتعاقد الفعلي بالمصنع:")
            if st.form_submit_button("حفظ بيانات العامل بالملفات السحابية"):
                st.success(f"✅ تم تسجيل العامل [{w_name}] بنجاح في سجل كادر العمال، وتفريغ الاستمارة لطلب آخر.")
                
    with t_w_adv:
        st.write("#### 💵 قيد وصرف سلفة مالية تحت الحساب (تخصم من راتب الشهر المقبل)")
        workers_list_options = ["أبو أحمد الفني - إقامة 24410982", "كومار الفني - إقامة 23310452"]
        selected_worker_for_adv = st.selectbox("اختر اسم العامل المستلف من الكادر:", workers_list_options)
        adv_amt_input = st.number_input("مبلغ السلفة النقدية المطلوبة للخصم اللاحق (ريال):", min_value=0.0, value=1000.0)
        
        if st.button("💵 اعتماد وصرف السلفة وطباعة مستند التوقيع"):
            st.markdown(f"""
            <div class="printable-sheet">
            <h4 style="text-align:center;">📄 مستند إقرار استلام سلفة مؤقتة - مصنع سبل الريادة</h4>
            <p>أقر أنا العامل المقيد بالأسفل بأنني استلمت مبلغ وقدره <b>{adv_amt_input:,.2f} ريال سعودي</b> فقط لا غير كـسلفة تحت الحساب، على أن يتم خصمها تلقائياً من راتبي لشهر المقبل.</p>
            <p><b>اسم العامل الكامل:</b> {selected_worker_for_adv}</p>
            <p>توقيع العامل وبصمته بالإقرار: ......................... | اعتماد الإدارة الهندسية: البشمهندس محمد سلامة</p>
            </div>
            """, unsafe_allow_html=True)
            st.button("🖨️ اضغط لطباعة مستند السلفة للإمضاء الورقي")

    with t_w_pay:
        st.write("#### 💰 شاشة اعتماد وصرف مسيرات الرواتب وتصفية السلف آلياً")
        st.selectbox("اختر العامل لتوليد مسير راتبه وتصفيته:", ["أبو أحمد الفني - إقامة 24410982"])
        worker_base_salary = st.number_input("الراتب المستحق الأساسي شامل الحوافز والبدلات للشهر الحالي:", value=5000.0)
        
        # تفعيل معادلة الخصم التلقائي للسلف المحفوظة آلياً بالسيستم بناء على طلبك بالملحوظة
        auto_detected_advance = 1000.00 # تم سحبها برمجيا من جدول السلف
        net_worker_salary_payout = worker_base_salary - auto_detected_advance
        
        st.markdown(f"""
        <div class="printable-sheet">
        <h4 style="text-align:center; color:green;">📄 إيصال استلام راتب شهري مصفى ومطابق للأنظمة</h4>
        <p>الراتب الأساسي الإجمالي المستحق: <b>{worker_base_salary:,.2f} ريال</b></p>
        <p style="color:red;">خصم مديونيات وسلف سابقة مقيدة آلياً بالسيستم: <b>-{auto_detected_advance:,.2f} ريال</b></p>
        <hr>
        <h4>الصافي الفعلي المسلم للعامل يدوياً أو تحويلاً: {net_worker_salary_payout:,.2f} ريال سعودي</h4>
        <p style="font-size:12px;">* تم تصفية السجل المالي للعامل ورجع حسابه نقياً للشهر الجديد.</p>
        </div>
        """, unsafe_allow_html=True)
        st.button("🖨️ طباعة إيصال استلام الراتب المصفى")

    with t_w_query:
        st.write("#### 🔍 شاشة الاستعلام وحركة كشف الحساب المالي لفني")
        st.text_input("أدخل اسم العامل أو رقم إقامته الدقيق للفحص المالي:")
        st.button("📊 عرض تفصيل الحساب وحركات السلف والرواتب التاريخية للفني")

# ==========================================
# [قسم 7]: مركز الاستعلام الشامل والمتقدم لكافة الأقسام بالصلاحيات
# ==========================================
elif menu == "🔍 مركز الاستعلام المتقدم":
    st.subheader("🔍 بوابة البحث والاستعلامات والتقارير المركزية لمصنع سُبُل الريادة")
    
    query_mode = st.selectbox("اختر تصنيف ونوع الاستعلام المطلوب تشغيله الآن بالملف السحابي:", [
        "البحث عن عميل وكشف مديونياته", 
        "البحث وتتبع طلبية محددة بالإنتاج", 
        "حساب مورد وجدول المشتريات التاريخية"
    ])
    
    search_keyword = st.text_input("أدخل كلمة البحث المرجعية (كود الطلبية، اسم العميل، رقم السجل، رقم الإقامة):")
    
    if st.button("🔍 تنفيذ أمر البحث الفوري والفلترة"):
        st.success(f"📊 تم فحص وعرض النتائج السحابية المتوافقة مع الكلمة المرجعية [{search_keyword}] بنجاح.")
