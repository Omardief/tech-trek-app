# Tech Trek - Full Streamlit App with Detailed Features

import streamlit as st
import pandas as pd
from datetime import date, datetime
from uuid import uuid4
import base64
from supabase import create_client, Client
import plotly.express as px
import pandas as pd
import pdfkit
import tempfile

# Supabase credentials
SUPABASE_URL = "https://cvbboynjicgobvljycdv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN2YmJveW5qaWNnb2J2bGp5Y2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzMzI5MTcsImV4cCI6MjA2NTkwODkxN30.pDwODqooOExR4aunB7dHj3nvyMXO7xT7qBV1pj0xT8s"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# === تخزين بيانات تسجيل الدخول في session ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# === صفحة تسجيل الدخول ===
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول")
    username = st.text_input("اسم المستخدم")
    password = st.text_input("كلمة المرور", type="password")
    
    if st.button("تسجيل الدخول"):
        users = supabase.table("users").select("*").eq("username", username).eq("password", password).execute().data
        if users:
            user = users[0]
            st.session_state.logged_in = True
            st.session_state.role = user["role"]
            st.session_state.username = user["username"]
            st.success("✅ تم تسجيل الدخول بنجاح")
            st.rerun()
        else:
            st.error("❌ بيانات غير صحيحة")

    st.stop()  # إيقاف الكود لحين تسجيل الدخول

@st.cache_data
def fetch_all_data():
    students = supabase.table("students").select("*").execute().data
    payments = supabase.table("payments").select("*").execute().data
    attendance = supabase.table("attendance").select("*").execute().data
    attendance_records = supabase.table("attendance_records").select("*").execute().data
    performance = supabase.table("performance").select("*").execute().data
    instructors = supabase.table("instructors").select("*").execute().data
    mentors = supabase.table("mentors").select("*").execute().data
    groups = supabase.table("groups").select("*").execute().data
    diplomas = supabase.table("diplomas").select("*").execute().data

    return {
        "students": students,
        "payments": payments,
        "attendance": attendance,
        "attendance_records": attendance_records,
        "performance": performance,
        "instructors": instructors,
        "mentors": mentors,
        "groups": groups,
        "diplomas": diplomas
    }

# تحميل البيانات
data = fetch_all_data()

# تحويل الدبلومات إلى dict
price_dict = {d["name"]: d["price"] for d in data["diplomas"]}

# Sidebar Navigation with Role-Based Access
st.sidebar.title("🧭 القائمة")

# === تحديد الصفحات المتاحة حسب الدور ===
if st.session_state.role == "admin":
    allowed_pages = [
        "📊 لوحة التحكم",
        "💼 التحليل المالي",
        "📋 إدارة الطالب",
        "إدارة الإنستراكتور والمينتور",
        "إدارة المجموعات",
        "📅 الحضور والتقييم",
        "عرض البيانات",
        "صفحة طالب"
    ]
elif st.session_state.role == "secretary":
    allowed_pages = [
        "📋 إدارة الطالب",
        "إدارة المجموعات",
        "📅 الحضور والتقييم",
        "صفحة طالب"
    ]
else:
    allowed_pages = []

# === اختيار الصفحة من الصفحات المسموحة فقط ===
page = st.sidebar.radio("اختر الشاشة", allowed_pages)

# === زر لتسجيل الخروج ===
if st.sidebar.button("🚪 تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.rerun()

# عنوان رئيسي ثابت
st.title("🎓 نظام إدارة تراك Tech Trek")


# Utility: Arabic-friendly Excel Export
@st.cache_data
def convert_df_to_excel(df):
    return df.to_csv(index=False, encoding='utf-8-sig')

# Utility: PDF export of student info (basic as HTML)
def create_download_link(html_content, filename):
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">📥 تحميل</a>'

if page == "📊 لوحة التحكم":
    st.header("📊 لوحة التحكم العامة")

    # === جلب البيانات مباشرة من Supabase ===
    students = supabase.table("students").select("*").execute().data
    payments = supabase.table("payments").select("*").execute().data
    attendance_data = supabase.table("attendance").select("*").execute().data

    # === الإحصائيات العامة ===
    total_students = len(students)
    active_students = sum(1 for s in students if s.get("status") == "نشط")
    withdrawn_students = sum(1 for s in students if s.get("status") == "منسحب")

    total_payments = sum(p.get("amount", 0) for p in payments)

    # استخراج عدد الجلسات
    sessions_by_diploma = {}
    for record in attendance_data:
        diploma = record.get("diploma")
        sessions = record.get("sessions", [])
        sessions_by_diploma[diploma] = sessions_by_diploma.get(diploma, []) + sessions
    total_sessions = sum(len(sessions) for sessions in sessions_by_diploma.values())

    # عرض المتريكس
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("👥 إجمالي الطلاب", total_students)
    col2.metric("✅ طلاب نشطين", active_students)
    col3.metric("❌ طلاب منسحبين", withdrawn_students)
    col4.metric("💰 إجمالي الدفعات", f"{total_payments:,} جنيه")
    col5.metric("🗓️ عدد الجلسات", total_sessions)

    # === تفاصيل حسب الدبلومة ===
    st.subheader("📚 تفاصيل حسب الدبلومة")
    for diploma in price_dict:
        diploma_students = [s for s in students if s.get("diploma") == diploma]
        diploma_student_names = [s["name"] for s in diploma_students]

        diploma_payments = sum(
            p.get("amount", 0)
            for p in payments
            if p.get("student") in diploma_student_names
        )

        diploma_sessions = len(sessions_by_diploma.get(diploma, []))

        with st.expander(f"🎓 {diploma}"):
            st.write(f"👥 عدد الطلاب: {len(diploma_students)}")
            st.write(f"💰 إجمالي الدفعات: {diploma_payments:,} جنيه")
            st.write(f"🗓️ عدد الجلسات: {diploma_sessions}")

    # === رسم بياني: تطور عدد الطلاب بمرور الوقت ===
    st.divider()
    st.subheader("📈 تطور عدد الطلاب بمرور الوقت")

    students_df = pd.DataFrame(students)
    if "created_at" in students_df.columns:
        students_df["created_at"] = pd.to_datetime(students_df["created_at"])
        daily_counts = students_df.groupby(students_df["created_at"].dt.date).size().reset_index(name="عدد الطلاب")
        fig_time = px.line(daily_counts, x="created_at", y="عدد الطلاب", markers=True, title="📆 عدد الطلاب حسب تاريخ التسجيل")
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("⚠️ لا يوجد حقل 'created_at' في بيانات الطلاب.")

    # === رسم بياني: توزيع الطلاب على الدبلومات ===
    st.divider()
    st.subheader("📊 توزيع الطلاب على الدبلومات")
    if "diploma" in students_df.columns:
        diploma_counts = students_df["diploma"].value_counts().reset_index()
        diploma_counts.columns = ["الدبلومة", "عدد الطلاب"]
        fig_diploma = px.pie(diploma_counts, names="الدبلومة", values="عدد الطلاب", title="🧪 توزيع الطلاب حسب الدبلومة", hole=0.4)
        st.plotly_chart(fig_diploma, use_container_width=True)

    # === رسم بياني: حالة الطلاب ===
    st.divider()
    st.subheader("📌 حالة الطلاب")
    if "status" in students_df.columns:
        status_counts = students_df["status"].value_counts().reset_index()
        status_counts.columns = ["الحالة", "عدد الطلاب"]
        fig_status = px.bar(status_counts, x="الحالة", y="عدد الطلاب", color="الحالة", title="📋 توزيع الطلاب حسب الحالة")
        st.plotly_chart(fig_status, use_container_width=True)

elif page == "💼 التحليل المالي":
    st.subheader("💼 لوحة التحكم المركزية")

    # === جلب البيانات من Supabase ===
    payments = supabase.table("payments").select("*").execute().data
    mentors = supabase.table("mentors").select("id", "name").execute().data
    instructors = supabase.table("instructors").select("id", "name").execute().data

    # === إجمالي الدخل ===
    total_income = sum(p.get("amount", 0) for p in payments)

    # === حساب رأس المال (10%) ===
    capital = round(total_income * 0.10)

    # === المتبقي بعد رأس المال ===
    remaining_after_capital = total_income - capital

    # === حساب نسبة Pioneer (40%) من المتبقي ===
    pioneer_share = round(remaining_after_capital * 0.40)

    # === الباقي بعد بايونير (60%) ===
    remaining_share_original = remaining_after_capital - pioneer_share

    # === خصم ما تم توزيعه فعليًا من جدول الإنستراكتور والمينتور ===
    instructor_paid = sum(r["amount"] for r in supabase.table("instructor_share").select("*").execute().data)
    mentor_paid = sum(r["amount"] for r in supabase.table("mentor_share").select("*").execute().data)

    remaining_share = remaining_share_original - instructor_paid - mentor_paid

    # === توزيع حسب طرق الدفع ===
    payments_by_method = {}
    for p in payments:
        method = p.get("method", "غير معروف")
        payments_by_method[method] = payments_by_method.get(method, 0) + p.get("amount", 0)

    # === عرض الملخص المالي في صف واحد ===
    st.markdown("### 💰 ملخص مالي")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("إجمالي الدخل", f"{total_income:,} جنيه")
    col2.metric("رأس المال (10%)", f"{capital:,} جنيه")
    col3.metric("Pioneer (40%)", f"{pioneer_share:,} جنيه")
    col4.metric("المتبقي للتوزيع (60%)", f"{remaining_share_original:,} جنيه")
    col5.metric("💼 المتبقي الآن", f"{remaining_share:,} جنيه")

    # === عرض طرق الدفع في صف واحد ===
    st.markdown("### 🧾 الدخل حسب طريقة الدفع")
    cash_col, insta_col, voda_col = st.columns(3)
    cash_col.metric("Cash", f"{payments_by_method.get('Cash', 0):,} جنيه")
    insta_col.metric("Instapay", f"{payments_by_method.get('Instapay', 0):,} جنيه")
    voda_col.metric("Vodafone Cash", f"{payments_by_method.get('Vodafone Cash', 0):,} جنيه")

    # === توزيع حصة الإنستراكتور ===
    st.divider()
    st.subheader("👨‍🏫 توزيع حصة الإنستراكتور")
    instructor_map = {i["name"]: i["id"] for i in instructors}
    selected_inst = st.selectbox("اختر الإنستراكتور", list(instructor_map.keys()))
    inst_amount = st.number_input("💵 المبلغ المخصص", min_value=0)

    if st.button("💾 حفظ توزيع الإنستراكتور"):
        if inst_amount > remaining_share:
            st.error("❌ المبلغ أكبر من المتبقي.")
        else:
            supabase.table("instructor_share").insert({
                "instructor_id": instructor_map[selected_inst],
                "amount": inst_amount,
                "date": datetime.now().isoformat()
            }).execute()
            st.success("✅ تم حفظ التوزيع.")
            st.rerun()

    # === توزيع حصة المينتور ===
    st.divider()
    st.subheader("🧑‍🏫 توزيع حصة المينتور")
    mentor_map = {m["name"]: m["id"] for m in mentors}
    selected_mentor = st.selectbox("اختر المينتور", list(mentor_map.keys()))
    mentor_amount = st.number_input("💵 المبلغ المخصص للمينتور", min_value=0, key="mentor")

    if st.button("💾 حفظ توزيع المينتور"):
        if mentor_amount > remaining_share:
            st.error("❌ المبلغ أكبر من المتبقي.")
        else:
            supabase.table("mentor_share").insert({
                "mentor_id": mentor_map[selected_mentor],
                "amount": mentor_amount,
                "date": datetime.now().isoformat()
            }).execute()
            st.success("✅ تم حفظ التوزيع.")
            st.rerun()

    # === تسجيل رأس المال وPioneer في الداتا بيز ===
    st.divider()
    st.subheader("📜 تسجيل رأس المال وPioneer")
    if st.button("📥 تسجيل رأس المال وPioneer"):
        supabase.table("academy_capital").insert({
            "amount": capital,
            "date": datetime.now().isoformat()
        }).execute()
        supabase.table("pioneer_share").insert({
            "amount": pioneer_share,
            "date": datetime.now().isoformat()
        }).execute()
        st.success("✅ تم تسجيل رأس المال وPioneer في قاعدة البيانات.")
       # === توزيع الأرباح على الشركاء ===
    st.divider()
    st.subheader("🤝 توزيع الأرباح على الشركاء")

    # جلب الشركاء من قاعدة البيانات
    project_managers = supabase.table("project_managers").select("*").execute().data
    pm_shares = supabase.table("project_manager_share").select("*").execute().data

    # جمع كل المبالغ المدفوعة سابقًا
    pm_distributed_total = sum(p["amount"] for p in pm_shares)

    # حساب المتبقي النهائي بعد الإنستراكتور والمينتور والشركاء
    true_remaining_share = remaining_share_original - instructor_paid - mentor_paid - pm_distributed_total

    # عرض المبالغ لكل شريك
    for pm in project_managers:
        name = pm["name"]
        percent = pm["percentage"]
        share_amount = round((remaining_share_original * percent) / 100)

        # عرض اسم الشريك والنسبة والناتج
        st.write(f"🔸 {name} - النسبة: {percent}% → المستحق: {share_amount:,} جنيه")

        if st.button(f"💾 حفظ توزيع {name}"):
            if share_amount > true_remaining_share:
                st.error("❌ المبلغ أكبر من المتبقي الحقيقي.")
            else:
                supabase.table("project_manager_share").insert({
                    "manager_id": pm["id"],
                    "amount": share_amount,
                    "date": datetime.now().isoformat()
                }).execute()
                st.success(f"✅ تم حفظ توزيع {name} - {share_amount:,} جنيه.")
                st.rerun()

    st.divider()
    st.markdown(f"### 🧾 <span style='color:red'>المتبقي بعد توزيع الإنستراكتور + المينتور + الشركاء: {true_remaining_share:,} جنيه</span>", unsafe_allow_html=True)


elif page == "إدارة الإنستراكتور والمينتور":
    st.header("👥 إدارة الإنستراكتور والمينتور")

    tab1, tab2 = st.tabs(["➕ إضافة إنستراكتور", "➕ إضافة مينتور"])

    # ===== إضافة إنستراكتور =====
    with tab1:
        with st.form("add_instructor_form"):
            name = st.text_input("👨‍🏫 اسم الإنستراكتور")
            phone = st.text_input("📞 رقم الهاتف")
            email = st.text_input("📧 البريد الإلكتروني")
            specialization = st.text_input("🧪 التخصص")
            start_date = st.date_input("🗓️ تاريخ البدء")
            
            mode = st.selectbox("🎯 نوع العمل", ["أونلاين", "أوفلاين", "الاثنين"])

            st.markdown("#### 💰 معلومات الحساب")
            pay_method = st.selectbox("طريقة الحساب", ["بالساعة", "بالسيشن", "نسبة مئوية"])
            pay_value = st.number_input("القيمة المالية", min_value=0.0, step=1.0)

            submit_instructor = st.form_submit_button("➕ حفظ الإنستراكتور")
            if submit_instructor:
                payload = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "specialization": specialization,
                    "start_date": str(start_date),
                    "pay_type": pay_method,
                    "rate": pay_value,
                    "mode": mode
                }
                response = supabase.table("instructors").insert(payload).execute()
                if response.data:
                    st.success(f"✅ تم إضافة الإنستراكتور {name} بنجاح!")
                    st.rerun()
                else:
                    st.error(f"❌ حدث خطأ أثناء الإضافة: {response.error.message if response.error else 'خطأ غير معروف'}")

        st.subheader("📋 قائمة الإنستراكتورز")

        # ✅ جلب البيانات من Supabase مباشرة
        instructors_response = supabase.table("instructors").select("*").execute()
        instructors_data = instructors_response.data

        if instructors_data:
            df = pd.DataFrame(instructors_data)
            st.dataframe(df[["name", "specialization", "mode", "pay_type", "rate"]])
        else:
            st.info("لا يوجد إنستراكتورز مسجلين بعد.")

    # ===== إضافة مينتور =====
    with tab2:
        with st.form("add_mentor_form"):
            name = st.text_input("👨‍💼 اسم المينتور")
            phone = st.text_input("📞 رقم الهاتف", key="mentor_phone")
            email = st.text_input("📧 البريد الإلكتروني", key="mentor_email")
            experience = st.text_area("📚 الخبرات")
            start_date = st.date_input("🗓️ تاريخ البدء", key="mentor_start")
            
            mode = st.selectbox("🎯 نوع العمل", ["أونلاين", "أوفلاين", "الاثنين"], key="mentor_mode")

            st.markdown("#### 💰 معلومات الحساب")
            pay_method = st.selectbox("طريقة الحساب", ["بالساعة", "بالسيشن", "نسبة مئوية"], key="mentor_pay_method")
            pay_value = st.number_input("القيمة المالية", min_value=0.0, step=1.0, key="mentor_pay_value")

            submit_mentor = st.form_submit_button("➕ حفظ المينتور")
            if submit_mentor:
                payload = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "experience": experience,
                    "start_date": str(start_date),
                    "pay_type": pay_method,
                    "rate": pay_value,
                    "mode": mode
                }
                response = supabase.table("mentors").insert(payload).execute()
                if response.data:
                    st.success(f"✅ تم إضافة المينتور {name} بنجاح!")
                    st.rerun()
                else:
                    st.error(f"❌ حدث خطأ أثناء إضافة المينتور: {response.error.message if response.error else 'خطأ غير معروف'}")

        st.subheader("📋 قائمة المينتورز")

        # ✅ جلب البيانات من Supabase مباشرة
        mentors_response = supabase.table("mentors").select("*").execute()
        mentors_data = mentors_response.data

        if mentors_data:
            df = pd.DataFrame(mentors_data)
            st.dataframe(df[["name", "mode", "pay_type", "rate"]])
        else:
            st.info("لا يوجد مينتورز مسجلين بعد.")


elif page == "إدارة المجموعات":
    st.header("🗂️ إدارة المجموعات")

    tab1, tab2 = st.tabs(["➕ إضافة وتعديل مجموعة", "👥 إضافة طلاب للمجموعة"])

    # تحميل البيانات من Supabase
    instructors = supabase.table("instructors").select("*").execute().data
    mentors = supabase.table("mentors").select("*").execute().data
    students = supabase.table("students").select("*").execute().data
    groups = supabase.table("groups").select("*").execute().data
    diplomas = supabase.table("diplomas").select("*").execute().data

    # تجهيز القواميس للاستخدام لاحقًا
    instructor_dict = {i["name"]: i["id"] for i in instructors}
    mentor_dict = {m["name"]: m["id"] for m in mentors}
    instructor_names = list(instructor_dict.keys())
    mentor_names = list(mentor_dict.keys())
    diploma_names = [d["name"] for d in diplomas]

    # تبويب 1: إضافة وتعديل مجموعة
    with tab1:
        with st.form("add_group_form"):
            group_name = st.text_input("اسم المجموعة")
            selected_diploma = st.selectbox("اختر الدبلومة", diploma_names)
            mode_choice = st.selectbox("نوع المجموعة", ["أونلاين", "أوفلاين", "الاثنين"])
            instructor_name = st.selectbox("اسم الإنستراكتور", instructor_names)
            mentor_name = st.selectbox("اسم المينتور", mentor_names)
            start_date = st.date_input("تاريخ بداية المجموعة", value=date.today())
            session_time = st.time_input("وقت الجلسة")

            submitted = st.form_submit_button("➕ إضافة المجموعة")
            if submitted:
                payload = {
                    "group_name": group_name,
                    "diploma": selected_diploma,
                    "mode": mode_choice,
                    "instructor_id": instructor_dict[instructor_name],
                    "mentor_id": mentor_dict[mentor_name],
                    "start_date": str(start_date),
                    "session_time": str(session_time),
                    "students": []
                }
                response = supabase.table("groups").insert(payload).execute()
                if response.data:
                    st.success(f"✅ تم إضافة المجموعة '{group_name}' بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ حدث خطأ أثناء حفظ المجموعة.")

        if groups:
            st.subheader("📋 قائمة المجموعات")

            # تجهيز جدول العرض باستبدال IDs بالأسماء
            def get_name_by_id(id_value, table_data):
                return next((item["name"] for item in table_data if item["id"] == id_value), "❓غير معروف")

            display_groups = []
            for g in groups:
                display_groups.append({
                    "اسم المجموعة": g["group_name"],
                    "الدبلومة": g.get("diploma", ""),
                    "نوع المجموعة": g.get("mode", ""),
                    "الإنستراكتور": get_name_by_id(g.get("instructor_id"), instructors),
                    "المينتور": get_name_by_id(g.get("mentor_id"), mentors),
                    "تاريخ البداية": g.get("start_date", ""),
                    "وقت الجلسة": g.get("session_time", "")
                })

            st.dataframe(pd.DataFrame(display_groups))

        else:
            st.info("لا توجد مجموعات مسجلة بعد.")

    # تبويب 2: إضافة طلاب للمجموعة
    with tab2:
        if not groups:
            st.warning("⚠️ لا توجد مجموعات. قم بإضافة مجموعة أولاً.")
        elif not students:
            st.warning("⚠️ لا يوجد طلاب مسجلين.")
        else:
            st.subheader("👥 إدارة طلاب المجموعة")
            group_names = [g["group_name"] for g in groups]
            selected_group = st.selectbox("اختر المجموعة", group_names, key="select_group_for_students")
            group_obj = next(g for g in groups if g["group_name"] == selected_group)

            # جلب بيانات الانستراكتور والمينتور من خلال ID
            instructor = next((i for i in instructors if i["id"] == group_obj.get("instructor_id")), None)
            mentor = next((m for m in mentors if m["id"] == group_obj.get("mentor_id")), None)

            if instructor:
                st.info(f"🎓 **الإنستراكتور:** {instructor['name']} — طريقة الحساب: {instructor['pay_type']} — أجره: {instructor['rate']}")
            if mentor:
                st.info(f"👨‍🏫 **المينتور:** {mentor['name']} — طريقة الحساب: {mentor['pay_type']} — أجره: {mentor['rate']}")

            current_students = group_obj.get("students", [])
            available_students = [s["name"] for s in students if s["name"] not in current_students]
            selected_students = st.multiselect("اختر الطلاب لإضافتهم", available_students)

            if st.button("📅 إضافة الطلاب إلى المجموعة"):
                updated_students = current_students + selected_students
                supabase.table("groups").update({"students": updated_students}).eq("group_name", selected_group).execute()
                st.success(f"✅ تم إضافة {len(selected_students)} طالب إلى المجموعة.")
                st.rerun()

            # عرض الطلاب داخل المجموعة + حذف طالب
            st.subheader("📃 الطلاب داخل المجموعة")
            if current_students:
                for student_name in current_students:
                    col1, col2 = st.columns([5, 1])
                    col1.write(f"👤 {student_name}")
                    if col2.button("🗑️ حذف", key=f"remove_{student_name}_{selected_group}"):
                        new_list = [s for s in current_students if s != student_name]
                        supabase.table("groups").update({"students": new_list}).eq("group_name", selected_group).execute()
                        st.success(f"✅ تم حذف {student_name} من المجموعة.")
                        st.rerun()
            else:
                st.info("لا يوجد طلاب حالياً في هذه المجموعة.")


elif page == "📋 إدارة الطالب":
    st.header("📋 إدارة الطالب")

    tabs = st.tabs(["🧾 تسجيل طالب جديد", "💰 تسجيل دفعة جديدة"])

    # تحميل البيانات مباشرة من Supabase
    groups = supabase.table("groups").select("*").execute().data
    students = supabase.table("students").select("*").execute().data

    with tabs[0]:
        st.subheader("🧾 تسجيل طالب جديد")

        with st.form("student_form"):
            name = st.text_input("اسم الطالب")
            phone = st.text_input("رقم التليفون")
            email = st.text_input("البريد الإلكتروني")
            diploma = st.selectbox("الدبلومة", list(price_dict.keys()))

            # فلترة الجروبات الخاصة بالدبلومة
            related_groups = [g for g in groups if g.get("diploma") == diploma]
            related_group_names = [g["group_name"] for g in related_groups]

            selected_group = st.selectbox("اختر المجموعة", related_group_names) if related_group_names else None

            if not related_group_names:
                st.warning("⚠️ لا توجد مجموعات مرتبطة بهذه الدبلومة، الرجاء إضافتها أولًا من إدارة المجموعات.")

            mode = st.radio("نظام الحضور", ["أونلاين", "أوفلاين"])

            price = price_dict[diploma]
            deposit = 500
            remaining = price - deposit

            registration_date = st.date_input("تاريخ التسجيل", value=date.today())
            start_date = st.date_input("تاريخ بدء الدبلومة", value=date.today())
            deposit_date = st.date_input("تاريخ دفع القسط المبدئي", value=date.today())
            deposit_method = st.selectbox("طريقة دفع القسط المبدئي", ["Cash", "Instapay", "Vodafone Cash"])
            status = st.selectbox("حالة الطالب", ["نشط", "منسحب", "مؤجل"])
            notes = st.text_area("ملاحظات إضافية")

            st.info(f"📌 السعر الكلي: {price} جنيه – القسط المبدئي: {deposit} جنيه – المتبقي: {remaining} جنيه")

            submitted = st.form_submit_button("تسجيل الطالب")
            if submitted:
                if not selected_group:
                    st.error("❌ لا يمكن تسجيل الطالب بدون اختيار مجموعة.")
                else:
                    student_code = f"{diploma[:2].upper()}-{str(uuid4())[:8]}"
                    group_id = next((g["id"] for g in related_groups if g["group_name"] == selected_group), None)

                    student_payload = {
                        "code": student_code,
                        "name": name,
                        "phone": phone,
                        "email": email,
                        "diploma": diploma,
                        "group_id": group_id,
                        "mode": mode,
                        "price": price,
                        "paid": deposit,
                        "remaining": remaining,
                        "deposit_date": str(deposit_date),
                        "deposit_method": deposit_method,
                        "registration_date": str(registration_date),
                        "start_date": str(start_date),
                        "status": status,
                        "notes": notes
                    }

                    student_res = supabase.table("students").insert(student_payload).execute()

                    if student_res.data:
                        student_id = student_res.data[0]["id"]  # الحصول على ID الطالب المضاف
                        # تسجيل الدفعة الأولى
                        payment_payload = {
                            "student_id": student_id,
                            "amount": deposit,
                            "date": str(deposit_date),
                            "method": deposit_method,
                            "note": "قسط مبدئي"
                        }
                        supabase.table("payments").insert(payment_payload).execute()
                        st.success("✅ تم تسجيل الطالب ودفع القسط المبدئي بنجاح")
                        st.rerun()
                    else:
                        st.error("❌ حدث خطأ أثناء التسجيل. يرجى المحاولة لاحقًا.")


    with tabs[1]:
        st.subheader("💰 تسجيل دفعة مالية جديدة")

        students_names = [s["name"] for s in students]
        if students_names:
            with st.form("payment_form"):
                selected_student_name = st.selectbox("اختر الطالب", students_names)
                amount = st.number_input("المبلغ المدفوع", min_value=0)
                pay_date = st.date_input("تاريخ الدفع", value=date.today())
                method = st.selectbox("طريقة الدفع", ["Cash", "Instapay", "Vodafone Cash"])
                note = st.text_input("ملاحظات الدفع (اختياري)")

                paid = st.form_submit_button("تسجيل الدفع")
                if paid:
                    # جلب بيانات الطالب باستخدام الاسم
                    student = next((s for s in students if s["name"] == selected_student_name), None)

                    if student:
                        student_id = student["id"]
                        total_paid = student["paid"] + amount
                        remaining = student["price"] - total_paid

                        if total_paid > student["price"]:
                            st.warning("⚠️ الطالب دفع أكثر من السعر المطلوب!")

                        # إنشاء الدفع
                        payment_payload = {
                            "student_id": student_id,
                            "amount": amount,
                            "date": str(pay_date),
                            "method": method,
                            "note": note
                        }
                        supabase.table("payments").insert(payment_payload).execute()

                        # تحديث بيانات الطالب
                        supabase.table("students").update({
                            "paid": total_paid,
                            "remaining": remaining
                        }).eq("id", student_id).execute()

                        st.success("✅ تم تسجيل الدفعة وتحديث بيانات الطالب")
                        st.rerun()
                    else:
                        st.error("❌ لم يتم العثور على بيانات الطالب.")
        else:
            st.warning("⚠️ لا يوجد طلاب مسجلين، قم بتسجيل طالب أولًا.")




elif page == "عرض البيانات":
    st.header("📋 عرض بيانات الطلاب والدفعات")

    # تحميل البيانات من Supabase
    students = supabase.table("students").select("*").execute().data
    payments = supabase.table("payments").select("*").execute().data
    attendance = supabase.table("attendance").select("*").execute().data
    attendance_records = supabase.table("attendance_records").select("*").execute().data
    performance = supabase.table("performance").select("*").execute().data

    st.subheader("📚 الطلاب")

    search = st.text_input("🔍 بحث عن اسم الطالب")
    selected_diploma = st.selectbox("🎓 اختر دبلومة", ["الكل"] + list(price_dict.keys()))
    selected_status = st.selectbox("📌 اختر الحالة", ["الكل", "نشط", "منسحب", "مؤجل"])

    # ===== فلترة الطلاب =====
    filtered_students = students.copy()
    if search:
        filtered_students = [s for s in filtered_students if search.lower() in s["name"].lower()]
    if selected_diploma != "الكل":
        filtered_students = [s for s in filtered_students if s["diploma"] == selected_diploma]
    if selected_status != "الكل":
        filtered_students = [s for s in filtered_students if s["status"] == selected_status]

    # ===== عرض الطلاب =====
    df_students = pd.DataFrame(filtered_students)
    st.dataframe(df_students)
    st.download_button("📥 تحميل الطلاب كـ Excel", convert_df_to_excel(df_students), file_name="students.xlsx")

    # ===== الدفعات =====
    st.subheader("💳 الدفعات")
    df_payments = pd.DataFrame(payments)
    st.dataframe(df_payments)
    st.download_button("📥 تحميل الدفعات كـ Excel", convert_df_to_excel(df_payments), file_name="payments.xlsx")

    # ===== تنبيهات الطلاب =====
    st.subheader("🚨 تنبيهات الطلاب")

    # حساب عدد الجلسات لكل دبلومة
    sessions_per_diploma = {a["diploma"]: len(a.get("sessions", [])) for a in attendance}

    # تجميع حضور الطلاب
    records_by_student = {}
    for record in attendance_records:
        student_id = record["student_id"]
        records_by_student.setdefault(student_id, []).append(record)

    # تجهيز التنبيهات
    alerts = []
    for s in filtered_students:
        student_id = s["id"]
        student_name = s["name"]
        student_diploma = s.get("diploma", "")
        alert_list = []

        # ❗ لم يدفع المبلغ كاملًا
        if s.get("remaining", 0) > 0:
            alert_list.append("❗ لم يدفع المبلغ كاملًا")

        # 📉 نسبة الحضور أقل من 50%
        total_sessions = sessions_per_diploma.get(student_diploma, 0)
        attended_sessions = len(records_by_student.get(student_id, []))
        if total_sessions > 0:
            attendance_rate = attended_sessions / total_sessions
            if attendance_rate < 0.5:
                alert_list.append(f"📉 نسبة الحضور {round(attendance_rate * 100)}%")

        # 📑 لا يوجد تقييمات
        student_evals = [e for e in performance if e["student_id"] == student_id]
        if not student_evals:
            alert_list.append("📑 لا يوجد تقييمات")

        if alert_list:
            alerts.append({
                "اسم الطالب": student_name,
                "الدبلومة": student_diploma,
                "الحالة": s.get("status", "غير معروف"),
                "التنبيهات": " | ".join(alert_list)
            })

    if alerts:
        alerts_df = pd.DataFrame(alerts)
        st.dataframe(alerts_df)
        st.download_button("📥 تحميل التنبيهات كـ Excel", convert_df_to_excel(alerts_df), file_name="alerts.xlsx")
    else:
        st.success("✅ لا توجد تنبيهات حالياً")


elif page == "📅 الحضور والتقييم":
    st.header("🎯 متابعة الحضور وتسجيل التقييم")

    tab1, tab2, tab3 = st.tabs(["🟢 تسجيل الحضور", "📝 تسجيل التقييم", "📊 إحصائيات الحضور"])

    # تحميل البيانات من Supabase
    students = supabase.table("students").select("*").execute().data
    attendance_data = supabase.table("attendance").select("*").execute().data
    attendance_records = supabase.table("attendance_records").select("*").execute().data
    performance_data = supabase.table("performance").select("*").execute().data

    student_dict = {s["name"]: s["id"] for s in students}
    id_to_name = {s["id"]: s["name"] for s in students}

    # ============ تبويب 1: تسجيل الحضور ============
    with tab1:
        selected_diploma = st.selectbox("اختر الدبلومة", list(price_dict.keys()), key="att_dip")
        students_in_diploma = [s for s in students if s["diploma"] == selected_diploma]

        if students_in_diploma:
            session_date = st.date_input("📅 تاريخ الجلسة", value=date.today())
            session_title = st.text_input("عنوان الجلسة (اختياري)")

            with st.form("attendance_form"):
                attendance_list = [s for s in students_in_diploma if st.checkbox(s["name"], key=f"{selected_diploma}_{session_date}_{s['id']}")]
                submitted = st.form_submit_button("✅ تسجيل الحضور")

                if submitted:
                    # 1. تحديث جدول attendance
                    supabase.table("attendance").upsert({
                        "diploma": selected_diploma,
                        "sessions": [{"date": str(session_date), "title": session_title}]
                    }, on_conflict=["diploma"]).execute()

                    # 2. حفظ كل حضور في جدول records
                    for student in attendance_list:
                        supabase.table("attendance_records").insert({
                            "student_id": student["id"],
                            "diploma": selected_diploma,
                            "date": str(session_date),
                            "title": session_title
                        }).execute()
                    st.success("✅ تم تسجيل حضور الجلسة")
        else:
            st.warning("⚠️ لا يوجد طلاب في هذه الدبلومة.")

    # ============ تبويب 2: تسجيل التقييم ============
    with tab2:
        if students:
            student_names = [s["name"] for s in students]
            selected_name = st.selectbox("اختر الطالب", student_names)
            student_id = student_dict[selected_name]

            task_type = st.selectbox("نوع التقييم", ["Assignment", "Quiz", "Project"])
            title = st.text_input("عنوان المهمة")
            grade = st.number_input("الدرجة / التقييم", min_value=0.0, max_value=100.0)
            date_given = st.date_input("تاريخ التسليم", value=date.today())

            if st.button("💾 حفظ التقييم"):
                supabase.table("performance").insert({
                    "student_id": student_id,
                    "type": task_type,
                    "title": title,
                    "grade": grade,
                    "date": str(date_given)
                }).execute()
                st.success("✅ تم تسجيل التقييم")
        else:
            st.warning("⚠️ لا يوجد طلاب.")

    # ============ تبويب 3: إحصائيات الحضور ============
    with tab3:
        for diploma in price_dict:
            st.subheader(f"🎓 {diploma}")
            students_in_diploma = [s for s in students if s["diploma"] == diploma]
            student_ids = [s["id"] for s in students_in_diploma]
            id_name_map = {s["id"]: s["name"] for s in students_in_diploma}

            diploma_sessions = [s for s in attendance_data if s["diploma"] == diploma]
            total_sessions = sum(len(d.get("sessions", [])) for d in diploma_sessions)

            if total_sessions == 0:
                st.info("🚫 لم يتم تسجيل أي جلسة.")
                continue

            stats = []
            for student_id in student_ids:
                attended = sum(1 for r in attendance_records if r["student_id"] == student_id and r["diploma"] == diploma)
                percentage = round(attended / total_sessions * 100, 2)
                stats.append({
                    "الطالب": id_name_map.get(student_id, "❓"),
                    "عدد الجلسات": total_sessions,
                    "حضر": attended,
                    "نسبة الحضور": f"{percentage}%"
                })

            df_stats = pd.DataFrame(stats).sort_values("نسبة الحضور", ascending=False)
            df_stats.reset_index(drop=True, inplace=True)
            df_stats.index += 1
            df_stats.insert(0, "الترتيب", df_stats.index)
            st.dataframe(df_stats)


elif page == "صفحة طالب":
    st.header("👤 صفحة طالب")

    # تحميل البيانات من Supabase
    students = supabase.table("students").select("*").execute().data
    groups = supabase.table("groups").select("*").execute().data
    payments = supabase.table("payments").select("*").execute().data
    attendance_records = supabase.table("attendance_records").select("*").execute().data
    attendance_sessions = supabase.table("attendance").select("*").execute().data
    evaluations = supabase.table("performance").select("*").execute().data

    student_options = [(s["id"], s["name"]) for s in students]

    if not student_options:
        st.warning("⚠️ لا يوجد طلاب.")
        st.stop()

    selected_id, selected_name = st.selectbox("اختر الطالب", student_options, format_func=lambda x: x[1])
    student = next(s for s in students if s["id"] == selected_id)

    # ========== بيانات الطالب ==========
    st.subheader("📄 بيانات الطالب")
    student_df = pd.DataFrame(list(student.items()), columns=["البيان", "القيمة"])
    st.dataframe(student_df)

    # ========== بيانات المجموعة ==========
    student_group = next((g for g in groups if selected_id in g.get("student_ids", [])), None)
    if student_group:
        st.info(f"🧾 ينتمي هذا الطالب إلى المجموعة: **{student_group['group_name']}**")
        st.markdown(f"🎓 **الإنستراكتور:** {student_group.get('instructor', 'غير معروف')}  \n👨‍🏫 **المينتور:** {student_group.get('mentor', 'غير معروف')}")
    else:
        st.warning("⚠️ هذا الطالب غير منسوب إلى أي مجموعة حالياً.")

    # ========== الدفعات ==========
    st.subheader("💰 الدفعات")
    student_payments = [p for p in payments if p.get("student_id") == selected_id]
    payments_df = pd.DataFrame(student_payments)
    if payments_df.empty:
        st.info("لا توجد دفعات مسجلة لهذا الطالب.")
    else:
        st.dataframe(payments_df)

    # ========== الحضور ==========
    st.subheader("✅ الحضور")
    diploma = student.get("diploma")
    diploma_attendance = next((a for a in attendance_sessions if a["diploma"] == diploma), None)
    session_rows = []

    if diploma_attendance and "sessions" in diploma_attendance:
        for i, session in enumerate(diploma_attendance["sessions"]):
            الحالة = "✅ حاضر" if any(
                r["student_id"] == selected_id and r["date"] == session["date"]
                for r in attendance_records
            ) else "❌ غائب"
            session_rows.append({
                "رقم الجلسة": i + 1,
                "التاريخ": session.get("date"),
                "الجلسة": session.get("title", ""),
                "الحالة": الحالة
            })

    df_att = pd.DataFrame(session_rows)
    if df_att.empty:
        st.info("لا يوجد حضور مسجل لهذا الطالب.")
        present_count = 0
        total_sessions = 0
    else:
        st.dataframe(df_att)
        if "الحالة" in df_att.columns:
            present_count = df_att["الحالة"].value_counts().get("✅ حاضر", 0)
            total_sessions = len(df_att)
        else:
            present_count = 0
            total_sessions = 0

    # ========== التقييمات ==========
    st.subheader("📑 التقييمات")
    student_evals = [e for e in evaluations if e.get("student_id") == selected_id]
    eval_df = pd.DataFrame(student_evals)
    if eval_df.empty:
        st.info("لا توجد تقييمات مسجلة.")
    else:
        st.dataframe(eval_df)

    # ========== تعديل البيانات ==========
    st.subheader("✏️ تعديل البيانات")
    with st.form("edit_student_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_phone = st.text_input("📱 رقم التليفون", value=student.get("phone", ""))
            new_email = st.text_input("📧 البريد الإلكتروني", value=student.get("email", ""))
            mode_options = ["أونلاين", "أوفلاين"]
            new_mode = st.selectbox("🖥️ نظام الحضور", mode_options, index=mode_options.index(student.get("mode", "أونلاين")))
            status_options = ["نشط", "منسحب", "مؤجل"]
            new_status = st.selectbox("📌 الحالة", status_options, index=status_options.index(student.get("status", "نشط")))
        with col2:
            new_notes = st.text_area("📝 ملاحظات", value=student.get("notes", ""))
            new_start = st.date_input("📅 تاريخ بدء الدبلومة", value=pd.to_datetime(student.get("start_date", date.today())))
            new_reg = st.date_input("📅 تاريخ التسجيل", value=pd.to_datetime(student.get("registration_date", date.today())))

        save = st.form_submit_button("💾 حفظ التعديلات")
        if save:
            updated_data = {
                "phone": new_phone,
                "email": new_email,
                "mode": new_mode,
                "status": new_status,
                "notes": new_notes,
                "start_date": str(new_start),
                "registration_date": str(new_reg),
            }
            supabase.table("students").update(updated_data).eq("id", selected_id).execute()
            st.success("✅ تم تحديث بيانات الطالب بنجاح")
            st.experimental_rerun()

    # ========== حذف الطالب ==========
    st.markdown("---")
    st.subheader("🗑️ حذف الطالب")
    st.error("⚠️ سيتم حذف الطالب وبياناته (الدفعات، الحضور، التقييمات).")

    if st.button("🚨 اضغط هنا لحذف الطالب نهائيًا"):
        with st.expander("هل أنت متأكد؟"):
            confirm = st.radio("تأكيد الحذف", ["لا", "نعم، احذف الطالب"], key="confirm_delete")
            if confirm == "نعم، احذف الطالب":
                supabase.table("students").delete().eq("id", selected_id).execute()
                supabase.table("payments").delete().eq("student_id", selected_id).execute()
                supabase.table("performance").delete().eq("student_id", selected_id).execute()
                supabase.table("attendance_records").delete().eq("student_id", selected_id).execute()

                for g in groups:
                    if selected_id in g.get("student_ids", []):
                        new_ids = [x for x in g["student_ids"] if x != selected_id]
                        supabase.table("groups").update({"student_ids": new_ids}).eq("id", g["id"]).execute()

                st.success("✅ تم حذف الطالب وجميع بياناته بنجاح.")
                st.experimental_rerun()

    # ========== تحميل التقرير كـ HTML ==========
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Tahoma, Arial; direction: rtl; }}
            h2 {{ color: #2E86C1; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: right; }}
            th {{ background-color: #f2f2f2; }}
            p {{ font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>📄 بيانات الطالب</h2>
        {student_df.to_html(index=False, escape=False)}

        <h2>💰 الدفعات</h2>
        {payments_df.to_html(index=False, escape=False) if not payments_df.empty else "<p>لا توجد دفعات مسجلة.</p>"}

        <h2>✅ الحضور</h2>
        <p>عدد الجلسات: {total_sessions} | عدد مرات الحضور: {present_count} جلسة</p>
        {df_att.to_html(index=False, escape=False) if not df_att.empty else "<p>لا يوجد سجل حضور بعد.</p>"}

        <h2>📑 التقييمات</h2>
        {eval_df.to_html(index=False, escape=False) if not eval_df.empty else "<p>لا توجد تقييمات مسجلة.</p>"}
    </body>
    </html>
    """

    # حفظ كـ HTML وتحميله
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html", encoding="utf-8") as temp_html:
        temp_html.write(html_content)
        html_path = temp_html.name

    # عرض زر التحميل
    with open(html_path, "rb") as f:
        st.download_button(
            label="📥 تحميل التقرير كـ HTML",
            data=f,
            file_name=f"student_report_{student['code']}.html",
            mime="text/html"
        )
