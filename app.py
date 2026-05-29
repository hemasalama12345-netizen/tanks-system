import streamlit as st
import pandas as pd
import datetime

# إعدادات الصفحة العامة للبرنامج
st.set_page_config(page_title="منظومة إدارة مصنع الخزانات الاحترافية", layout="wide", initial_sidebar_state="expanded")

# تطبيق تصفيف CSS لدعم اللغة العربية والاتجاه من اليمين لليسار
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
    html, body, [data-testid="stSidebar"], .stApp {
        font-family: 'Cairo', sans-serif;
        direction: RTL;
        text-align: right;
    }
    .stMetric {
        text-align: center;
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    </style>
""", unsafe_allow_html=True)

# الثوابت المالية للمشروع
سعر_البيع = 4000
تكلفة_الخزان = 2705
نسبة_المقدم = 0.15

# تهيئة قاعدة البيانات المؤقتة في ذاكرة النظام (Session State)
if 'inventory' not in st.session_state:
    st.session_state.inventory = {"راتنج (طن)": 50.0, "فايبر (طن)": 20.0, "مصلد (كجم)": 500.0}
if 'production_log' not in st.session_state:
    st.session_state.production_log = []
if 'invoices' not in st.session_state:
    st.session_state.invoices = []
if 'supplier_balance' not in st.session_state:
    st.session_state.supplier_balance = 0.0

# القائمة الجانبية للتنقل بين أقسام البرنامج
st.sidebar.title("🛠️ لوحة التحكم والمراقبة")
st.sidebar.write("---")
القسم = st.sidebar.radio("انتقل إلى القسم:", [
    "📊 لوحة التحكم العامة (Dashboard)",
    "🏭 خط الإنتاج وتوليد الـ QR",
    "🧾 المبيعات وفواتير العملاء",
    "📦 المخازن وحسابات الموردين"
])

# ==========================================
# 1. قسم لوحة التحكم العامة
# ==========================================
if القسم == "📊 لوحة التحكم العامة (Dashboard)":
    st.title("📊 منظومة إدارة مشروع الـ 1,000 خزان")
    st.subheader("نظرة عامة على الأداء المالي والتشغيلي لحظة بلحظة")
    
    # حساب الإحصائيات
    إجمالي_المنتج = len(st.session_state.production_log)
    إجمالي_المبيعات = sum([inv['الصافي'] for inv in st.session_state.invoices])
    الكاش_المحصل = sum([inv['الصافي'] for inv in st.session_state.invoices if inv['الحالة'] == "تم التحصيل"])
    الكاش_المتأخر = إجمالي_المبيعات - الكاش_المحصل
    
    # عرض العدادات الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="إجمالي الإنتاج الفعلي", value=f"{إجمالي_المنتج} خزان")
    with col2:
        st.metric(label="إجمالي قيمة الفواتير", value=f"{إجمالي_المبيعات:,.2f} ريال")
    with col3:
        st.metric(label="الكاش الداخل للخزنة", value=f"{الكاش_المحصل:,.2f} ريال")
    with col4:
        st.metric(label="مستحقات متأخرة بالسوق", value=f"{الكاش_المتأخر:,.2f} ريال")
        
    st.write("---")
    st.subheader("📈 أحدث حركات الإنتاج بالمصنع")
    if st.session_state.production_log:
        df_prod = pd.DataFrame(st.session_state.production_log)
        st.dataframe(df_prod[["المسلسل", "التاريخ", "النوع", "المشرف"]], use_container_width=True)
    else:
        st.warning("لا توجد حركات إنتاج مسجلة اليوم.")

# ==========================================
# 2. قسم خط الإنتاج وتوليد الـ QR
# ==========================================
elif القسم == "🏭 خط الإنتاج وتوليد الـ QR":
    st.title("🏭 قسم مراقبة الجودة والإنتاج اللحظي")
    st.subheader("تسجيل الخزانات الجاهزة وتوليد الباركود تلقائياً")
    
    with st.form("production_form"):
        مشرف_الوردية = st.text_input("اسم مهندس / مشرف الوردية:")
        كمية_الإنتاج = st.number_input("عدد الخزانات الجاهزة للفحص الفني:", min_value=1, max_value=8, value=4)
        نوع_الخزان = st.selectbox("مواصفة المنتج:", ["خزان GRP - سعة 8,000 لتر دفن", "خزان GRP - سعة 8,000 لتر سطحي"])
        submit = st.form_submit_button("اعتماد الإنتاج وطباعة الـ QR")
        
        if submit and مشرف_الوردية:
            # معادلة خصم الخامات (افتراضية لكل خزان: 0.25 طن راتنج، 0.1 طن فايبر، 3 كجم مصلد)
            راتنج_مطلوب = كمية_الإنتاج * 0.25
            فايبر_مطلوب = كمية_الإنتاج * 0.1
            مصلد_مطلوب = كمية_الإنتاج * 3.0
            
            if st.session_state.inventory["راتنج (طن)"] >= راتنج_مطلوب and st.session_state.inventory["فايبر (طن)"] >= فايبر_مطلوب:
                # خصم المواد الخام من المخزن
                st.session_state.inventory["راتنج (طن)"] -= راتنج_مطلوب
                st.session_state.inventory["فايبر (طن)"] -= فايبر_مطلوب
                st.session_state.inventory["مصلد (كجم)"] -= مصلد_مطلوب
                
                # توليد الخزانات والأكواد
                for _ in range(كمية_الإنتاج):
                    مسلسل_فريد = f"TANK-8K-{datetime.datetime.now().strftime('%Y%m%d')}-{len(st.session_state.production_log) + 1:04d}"
                    st.session_state.production_log.append({
                        "المسلسل": مسلسل_فريد,
                        "التاريخ": str(datetime.date.today()),
                        "النوع": نوع_الخزان,
                        "المشرف": مشرف_الوردية
                    })
                st.success(f"✅ تم تسجيل {كمية_الإنتاج} خزانات بنجاح! وتحديث المخازن تلقائياً.")
            else:
                st.error("🚨 رصيد المواد الخام في المخزن لا يكفي لتصنيع هذه الكمية!")

    # عرض الخزانات المنتجة وروابط الـ QR الخاصة بها
    if st.session_state.production_log:
        st.write("---")
        st.subheader("🖨️ الأكواد الجاهزة للطباعة واللصق على الخزانات:")
        cols = st.columns(3)
        for idx, item in enumerate(st.session_state.production_log[-8:]): # عرض آخر 8 خزانات فقط
            with cols[idx % 3]:
                st.info(f"كود: {item['المسلسل']}")
                # توليد كود QR عبر رابط خارجي آمن وسريع لعرض البيانات عند الفحص
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={item['المسلسل']}-{item['النوع']}"
                st.image(qr_url, caption="امسح الباركود للتحقق من الجودة والشحن")

# ==========================================
# 3. قسم المبيعات وفواتير العملاء
# ==========================================
elif القسم == "🧾 المبيعات وفواتير العملاء":
    st.title("🧾 نظام الفواتير الذكي وتدفقات الكاش")
    st.subheader("توليد فواتير الشحن مع الخصم التلقائي للمقدم (15%)")
    
    col_inv1, col_inv2 = st.columns([1, 2])
    
    with col_inv1:
        st.subheader("إصدار فاتورة شحنة جديدة")
        اسم_العميل = st.text_input("اسم العميل / شركة المقاولات:", value="شركة المقاولات الرئيسية")
        الكمية_المشحونة = st.number_input("عدد الخزانات المشحونة في هذه الدفعة:", min_value=1, max_value=50, value=8)
        حالة_التحصيل = st.selectbox("حالة السداد الفوري للفاتورة:", ["لم يتم", "تم التحصيل"])
        توليد_فاتورة = st.button("إصدار الفاتورة المعتمدة")
        
        if توليد_فاتورة:
            الإجمالي = الكمية_المشحونة * سعر_البيع
            الخصم = الإجمالي * نسبة_المقدم
            الصافي = الإجمالي - الخصم
            
            st.session_state.invoices.append({
                "رقم_الفاتورة": len(st.session_state.invoices) + 101,
                "العميل": اسم_العميل,
                "الكمية": الكمية_المشحونة,
                "الإجمالي": الإجمالي,
                "الخصم_15": الخصم,
                "الصافي": الصافي,
                "التاريخ": str(datetime.date.today()),
                "تاريخ_الاستحقاق": str(datetime.date.today() + datetime.timedelta(days=10)),
                "الحالة": حالة_التحصيل
            })
            st.success("تم إصدار الفاتورة وتحديث كشف حساب العميل.")

    with col_inv2:
        st.subheader("📂 أرشيف الفواتير ومتابعة التحصيل (10 أيام)")
        if st.session_state.invoices:
            df_inv = pd.DataFrame(st.session_state.invoices)
            st.dataframe(df_inv[["رقم_الفاتورة", "العميل", "الكمية", "الصافي", "تاريخ_الاستحقاق", "الحالة"]], use_container_width=True)
            
            # اختيار فاتورة معينة لعرضها بشكل احترافي للطباعة
            فاتورة_المعاينة = st.selectbox("اختر رقم الفاتورة لعرضها بنظام اللوجو والطباعة:", df_inv["رقم_الفاتورة"].tolist())
            
            if فاتورة_المعاينة:
                selected_inv = [i for i in st.session_state.invoices if i["رقم_الفاتورة"] == فاتورة_المعاينة][0]
                
                st.write("---")
                # قالب الفاتورة الإحترافي HTML المصمم للطباعة مباشرة
                invoice_template = f"""
                <div style="border: 2px solid #333; padding: 20px; border-radius: 10px; background-color: #fff; color: #000; direction: rtl; text-align: right;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td><h2>شركة مصنع الخزانات الوطنية</h2><p>الرياض - المملكة العربية السعودية</p></td>
                            <td style="text-align: left;"><h1>فاتورة ضريبية</h1><p>رقم الفاتورة: #{selected_inv['رقم_الفاتورة']}</p><p>التاريخ: {selected_inv['التاريخ']}</p></td>
                        </tr>
                    </table>
                    <hr style="border: 1px solid #333;">
                    <p><strong>موجّه إلى السادة:</strong> {selected_inv['العميل']}</p>
                    <table style="width: 100%; border: 1px solid #333; border-collapse: collapse; text-align: center;">
                        <tr style="background-color: #f2f2f2;">
                            <th style="border: 1px solid #333; padding: 8px;">البيان</th>
                            <th style="border: 1px solid #333; padding: 8px;">الكمية</th>
                            <th style="border: 1px solid #333; padding: 8px;">سعر الوحدة</th>
                            <th style="border: 1px solid #333; padding: 8px;">الإجمالي</th>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #333; padding: 8px;">خزانات فيبرجلاس GRP سعة 8,000 لتر بمواصفات هندسية معتمدة</td>
                            <td style="border: 1px solid #333; padding: 8px;">{selected_inv['الكمية']}</td>
                            <td style="border: 1px solid #333; padding: 8px;">4,000 ريال</td>
                            <td style="border: 1px solid #333; padding: 8px;">{selected_inv['الإجمالي']:,.2f} ريال</td>
                        </tr>
                    </table>
                    <br>
                    <table style="width: 40%; float: left; text-align: right; font-weight: bold;">
                        <tr><td>الإجمالي قبل الخصم:</td><td>{selected_inv['الإجمالي']:,.2f} ريال</td></tr>
                        <tr><td style="color: red;">خصم الدفعة المقدمة (15%):</td><td style="color: red;">-{selected_inv['الخصم_15']:,.2f} ريال</td></tr>
                        <tr style="border-top: 2px solid #000; font-size: 18px;"><td>الصافي المطلوب كاش:</td><td>{selected_inv['الصافي']:,.2f} ريال</td></tr>
                    </table>
                    <div style="clear: both;"></div>
                    <br>
                    <p style="font-size: 12px; text-align: center; color: #555;">تاريخ استحقاق السداد كحد أقصى بموجب العقد: {selected_inv['تاريخ_الاستحقاق']}</p>
                </div>
                """
                st.markdown(invoice_template, unsafe_allow_html=True)
                st.write("💡 نصيحة: يمكنك الضغط على (Ctrl + P) لحفظ الفاتورة كـ PDF وطباعتها بلوجو الشركة.")
        else:
            st.info("لا توجد فواتير صادرة حتى الآن.")

# ==========================================
# 4. قسم المخازن وحسابات الموردين
# ==========================================
elif القسم == "📦 المخازن وحسابات الموردين":
    st.title("📦 إدارة المستودعات وحسابات الموردين")
    st.subheader("مراقبة أرصدة الخامات وتحديث الفواتير الآجلة")
    
    col_mat1, col_mat2 = st.columns(2)
    
    with col_mat1:
        st.subheader("📊 أرصدة الخامات الحالية بالمستودع")
        for key, val in st.session_state.inventory.items():
            if val < 5.0 and "طن" in key:
                st.error(f"⚠️ {key}: {val} (المخزون حرج! بحاجة لإعادة طلب)")
            else:
                st.success(f"✅ {key}: {val}")
                
    with col_mat2:
        st.subheader("🚚 توريد مواد خام جديدة (آجل / كاش)")
        المورد = st.text_input("اسم شركة التوريد:")
        قيمة_الفاتورة = st.number_input("إجمالي قيمة فاتورة الشراء (ريال):", min_value=0.0, value=50000.0)
        نوع_السداد = st.selectbox("طريقة الدفع للمورد:", ["كاش فوراً", "آجل / على الحساب"])
        تحديث_المخزن = st.button("تأكيد دخول الشحنة للمخزن")
        
        if تحديث_المخزن and المورد:
            if نوع_السداد == "آجل / على الحساب":
                st.session_state.supplier_balance += قيمة_الفاتورة
                st.success(f"تم تسجيل الفاتورة في حساب الآجل للمورد. إجمالي مستحقات الموردين الحالية: {st.session_state.supplier_balance:,.2f} ريال")
            else:
                st.success(f"تم تسجيل المدفوعات النقديّة للمورد بنجاح!")
            
            # زيادة افتراضية للمخزن لتجربة البرنامج
            st.session_state.inventory["راتنج (طن)"] += 10.0
            st.session_state.inventory["فايبر (طن)"] += 5.0