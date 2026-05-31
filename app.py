import streamlit as st
import pandas as pd
from datetime import datetime

# 1. إعدادات الصفحة العامة للتطبيق
st.set_page_config(
    page_title="نظام إدارة مصنع سُبُل الريادة",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تصميم وتنسيق الواجهة باللغة العربية
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 95%; }
    h1, h2, h3, p, div, span, label { text-align: right; direction: rtl; font-family: 'Cairo', sans-serif; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# 2. إنشاء الاتصال الآمن بقاعدة البيانات (Neon)
@st.cache_resource
def get_db_connection():
    try:
        # يقرأ تلقائياً الإعدادات من المربع الأسود (Secrets)
        return st.connection("postgresql", type="sql")
    except Exception as e:
        st.sidebar.error(f"فشل الاتصال بقاعدة البيانات: {e}")
        return None

conn = get_db_connection()

# 3. القائمة الجانبية للتنقل بين أقسام المصنع
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4080/4080032.png", width=80)
st.sidebar.title("مصنع سُبُل الريادة")
st.sidebar.write("نظام إدارة الإنتاج والمخازن السحابي")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "انتقل إلى القسم:",
    [
        "📊 لوحة التحكم الرئيسية",
        "📦 فتح وإدارة الطلبيات",
        "🪵 مخازن المواد الخام",
        "🔢 الإنتاج والأرقام التسلسلية",
        "💼 شؤون الموظفين والرواتب",
        "👥 دليل العملاء والموردين"
    ]
)

# ==========================================
# القسم الأول: لوحة التحكم الرئيسية (Dashboard)
# ==========================================
if menu == "📊 لوحة التحكم الرئيسية":
    st.title("📊 لوحة المؤشرات والأداء العام")
    st.write("ملخص رقمي فوري لحالة المصنع الحالية")
    st.markdown("---")
    
    # تهيئة المتغيرات الحسابية بأصفار (لحماية الكود من الشاشة الحمراء لو الداتابيز فارغة)
    total_order_val = 0.0
    active_orders_count = 0
    total_raw_materials = 0
    total_salaries_due = 0.0

    if conn is not None:
        # جلب البيانات بأمان مع معالجة الأخطاء لو الجداول فارغة
        try:
            df_orders = conn.query("SELECT SUM(order_value) as total, COUNT(*) as count FROM orders;", ttl=0)
            if not df_orders.empty:
                if df_orders.iloc[0]['total'] is not None:
                    total_order_val = float(df_orders.iloc[0]['total'])
                if df_orders.iloc[0]['count'] is not None:
                    active_orders_count = int(df_orders.iloc[0]['count'])
        except Exception:
            pass

        try:
            df_inv = conn.query("SELECT SUM(quantity) as total FROM inventory;", ttl=0)
            if not df_inv.empty and df_inv.iloc[0]['total'] is not None:
                total_raw_materials = int(df_inv.iloc[0]['total'])
        except Exception:
            pass

        try:
            df_salaries = conn.query("SELECT SUM(net_salary) as total FROM salaries;", ttl=0)
            if not df_salaries.empty and df_salaries.iloc[0]['total'] is not None:
                total_salaries_due = float(df_salaries.iloc[0]['total'])
        except Exception:
            pass

    # عرض كروت المؤشرات الرقمية (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="💰 إجمالي قيمة العقود والطلبيات", value=f"{total_order_val:,.2f} ريال")
    with col2:
        st.metric(label="📋 عدد الطلبيات النشطة", value=f"{active_orders_count} طلبية")
    with col3:
        st.metric(label="🪵 رصيد المواد الخام بالمخزن", value=f"{total_raw_materials} وحدة")
    with col4:
        st.metric(label="💵 إجمالي مسيرات الرواتب الحالية", value=f"{total_salaries_due:,.2f} ريال")

    st.markdown("---")
    
    # رسم بياني توضيحي أو ترحيبي
    st.subheader("⚙️ حالة خطوط الإنتاج والعمليات")
    st.info("نظام المصنع متصل الآن بنجاح بسيرفر Neon السحابي الآمن. يمكنك البدء في إدخال البيانات من الأقسام الجانبية.")

# ==========================================
# القسم الثاني: فتح وإدارة الطلبيات
# ==========================================
elif menu == "📦 فتح وإدارة الطلبيات":
    st.title("📦 فتح وإدارة طلببيات وعقود العملاء")
    st.write("شاشة تسجيل العقود الجديدة ومتابعة حالة الطلبات القائمة")
    st.markdown("---")
    
    # نموذج لإضافة طلبية جديدة
    with st.expander("➕ تسجيل أمر توريد / عقد جديد", expanded=False):
        with st.form("add_order_form"):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("اسم العميل / الشركة:")
                order_value = st.number_input("قيمة العقد المالي (ريال):", min_value=0.0, step=100.0)
            with col2:
                product_type = st.text_input("نوع المنتج المطلوبة (GRP / BMC / إلخ):")
                order_date = st.date_input("تاريخ التعاقد:", datetime.now())
                
            submit_order = st.form_submit_button("حفظ وتأكيد أمر التوريد")
            
            if submit_order and conn is not None:
                if customer_name and product_type:
                    try:
                        # إدخال البيانات في جدول الطلبيات
                        query = f"""
                            INSERT INTO orders (customer_name, product_type, order_value, order_date) 
                            VALUES ('{customer_name}', '{product_type}', {order_value}, '{order_date}');
                        """
                        conn.execute(query)
                        st.success(f"تم تسجيل عقد العميل {customer_name} بنجاح في قاعدة البيانات!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"حدث خطأ أثناء الحفظ: {e}")
                else:
                    st.warning("يرجى ملء جميع الحقول الأساسية قبل الحفظ.")

    # عرض الطلبيات الحالية
    st.subheader("📋 سجل أوامر التوريد الحالية")
    if conn is not None:
        try:
            df_all_orders = conn.query("SELECT * FROM orders ORDER BY order_date DESC;", ttl=0)
            if not df_all_orders.empty:
                st.dataframe(df_all_orders, use_container_width=True)
            else:
                st.info("لا توجد طلببيات مسجلة حالياً. استخدم النموذج أعلاه لإضافة أول عقد.")
        except Exception as e:
            st.error(f"خطأ أثناء قراءة جدول الطلبيات: {e}")

# ==========================================
# القسم الثالث: مخازن المواد الخام
# ==========================================
elif menu == "🪵 مخازن المواد الخام":
    st.title("🪵 مراقبة مخازن المواد الخام والكميات")
    st.write("متابعة المخزون الوارد والمنصرف لعمليات التصنيع")
    st.markdown("---")
    
    with st.expander("➕ توريد مواد خام جديدة للمخزن", expanded=False):
        with st.form("add_inventory_form"):
            col1, col2 = st.columns(2)
            with col1:
                item_name = st.text_input("اسم المادة الخام (مثال: ريزين / فيبرجلاس):")
                quantity = st.number_input("الكمية الموردة:", min_value=0, step=1)
            with col2:
                unit = st.text_input("وحدة القياس (كجم / طن / متر):")
                supplier = st.text_input("اسم المورد الرئيسي:")
                
            submit_inv = st.form_submit_button("تحديث رصيد المخزن")
            
            if submit_inv and conn is not None:
                if item_name:
                    try:
                        query = f"""
                            INSERT INTO inventory (item_name, quantity, unit, supplier) 
                            VALUES ('{item_name}', {quantity}, '{unit}', '{supplier}');
                        """
                        conn.execute(query)
                        st.success(f"تم إضافة {quantity} {unit} من {item_name} للمخازن.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"خطأ أثناء الحفظ: {e}")

    st.subheader("📦 الجرد الفوري للمواد الخام المتوفرة")
    if conn is not None:
        try:
            df_inv = conn.query("SELECT * FROM inventory;", ttl=0)
            if not df_inv.empty:
                st.dataframe(df_inv, use_container_width=True)
            else:
                st.info("المخزن فارغ حالياً. قم بتسجيل الوارد أولاً.")
        except Exception as e:
            st.error(f"خطأ في قراءة بيانات المخزن: {e}")

# ==========================================
# القسم الرابع: الإنتاج والأرقام التسلسلية
# ==========================================
elif menu == "🔢 الإنتاج والأرقام التسلسلية":
    st.title("🔢 تتبع الإنتاج والأرقام التسلسلية للمنتجات")
    st.write("توليد وتتبع السيريال نمبر الخاص بالمنتجات لضمان الجودة والتتبع")
    st.markdown("---")
    
    with st.form("serial_form"):
        col1, col2 = st.columns(2)
        with col1:
            serial_code = st.text_input("الرقم التسلسلي (Serial Number):")
            product_spec = st.text_input("مواصفات المقاس والنوع:")
        with col2:
            production_line = st.text_input("خط الإنتاج أو الفني المسؤول:")
            status = st.selectbox("حالة الفحص والمطابقة للجودة:", ["مطابق للمواصفات", "تحت الفحص", "مرفوض"])
            
        submit_serial = st.form_submit_button("تسجيل السيريال في سجل الإنتاج")
        
        if submit_serial and conn is not None:
            if serial_code:
                try:
                    query = f"""
                        INSERT INTO serial_numbers (serial_code, product_spec, production_line, status) 
                        VALUES ('{serial_code}', '{product_spec}', '{production_line}', '{status}');
                    """
                    conn.execute(query)
                    st.success(f"تم حظر وتوثيق السيريال {serial_code} بنجاح!")
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ أثناء التسجيل: {e}")

    st.subheader("🏭 سجل قطع الغيار والمنتجات ذات الرقم التسلسلي")
    if conn is not None:
        try:
            df_serials = conn.query("SELECT * FROM serial_numbers;", ttl=0)
            if not df_serials.empty:
                st.dataframe(df_serials, use_container_width=True)
            else:
                st.info("لا توجد قطع مسجلة بسيريال نمبر حتى الآن.")
        except Exception as e:
            st.error(f"خطأ في تتبع السيريال: {e}")

# ==========================================
# القسم الخامس: شؤون الموظفين والرواتب
# ==========================================
elif menu == "💼 شؤون الموظفين والرواتب":
    st.title("💼 إدارة شؤون الموظفين ومسيرات الرواتب")
    st.write("حساب رواتب الفنيين والعمال في المصنع وتوثيق مستحقاتهم")
    st.markdown("---")
    
    if conn is not None:
        try:
            df_salaries = conn.query("SELECT * FROM salaries;", ttl=0)
            if not df_salaries.empty:
                st.dataframe(df_salaries, use_container_width=True)
            else:
                st.info("لم يتم تسجيل أي مسيرات رواتب للشهر الحالي في جدول العمال بعد.")
        except Exception as e:
            st.error(f"خطأ في قراءة مسيرات الرواتب: {e}")

# ==========================================
# القسم السادس: دليل العملاء والموردين
# ==========================================
elif menu == "👥 دليل العملاء والموردين":
    st.title("👥 دليل جهات الاتصال (العملاء والموردين)")
    st.write("إدارة بيانات التواصل والشركات الشريكة مع مصنع سُبُل الريادة")
    st.markdown("---")
    
    if conn is not None:
        try:
            df_contacts = conn.query("SELECT * FROM customers;", ttl=0)
            if not df_contacts.empty:
                st.dataframe(df_contacts, use_container_width=True)
            else:
                st.info("الدليل فارغ حالياً. بمجرد إضافة العملاء من شاشة الطلبيات سيظهرون هنا.")
        except Exception as e:
            st.error(f"خطأ في قراءة دليل الاتصال: {e}")
