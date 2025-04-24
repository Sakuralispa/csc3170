from flask import Flask, session, redirect, url_for, request, render_template
import pymysql
import os
from dotenv import load_dotenv
import requests
import re

load_dotenv()

app = Flask(__name__)
USERNAME = 'admin'
PASSWORD = '123456'

# MySQL 配置
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 连接数据库

def get_db_connection():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        db=MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

# 调用 DeepSeek 模型

def call_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
            "role": "system",
            "content": """你是一个会写 MySQL 查询语句的助手。你只能使用以下数据库结构，请根据表名和字段生成 SQL，不要解释，直接输出标准 SQL 语句。表名和字段名区分大小写，请严格使用以下结构：

            表名：Student（学生）
            - Student_ID（学号，主键）
            - Name（姓名）
            - Gender（性别，char(1)）
            - Enrollment_Year（入学年份）
            - Dorm_ID（当前宿舍，外键 → Dorm.Dorm_ID）
            - Asset_ID（当前床位，外键 → Asset.Asset_ID，限定 Type='床'）
            - Phone（电话）
            - Status（在读/休学/毕业等状态）
            - Tutor_ID（负责老师，外键 → Tutor.Tutor_ID）

            表名：Dorm（宿舍）
            - Dorm_ID（门牌号，主键）
            - Dorm_Type（双人间/四人间）
            - Max_Capacity（最大容量）
            - Air_Conditioner（是否有空调，布尔）
            - Fan（是否有风扇，布尔）
            - Building_ID（所在楼栋，外键 → Building.Building_ID）

            表名：Building（楼栋）
            - Building_ID（楼栋号，主键）
            - Floor_Count（楼层数量）
            - Warden_ID（舍监，外键 → Warden.Warden_ID）
            - Location（地理位置）

            表名：Warden（舍监）
            - Warden_ID（舍监编号，主键）
            - Name（姓名）
            - Phone（联系方式）
            - Hire_Date（任职时间）

            表名：Activity（活动）
            - Activity_ID（活动ID，主键）
            - Title（活动标题）
            - Time（活动时间）
            - Location（地点）
            - Warden_ID（审批和负责老师，外键 → Tutor.Tutor_ID）
            - Capacity（人数上限）

            表名：Asset（资产）
            - Asset_ID（资产编号，主键）
            - Type（资产类型，如空调、椅子、床）
            - Status（状态：正常/报废/检修中）
            - Purchase_Date（购入时间）
            - Dorm_ID（当前宿舍，可为空，外键 → Dorm.Dorm_ID）
            - Building_ID（当前楼栋，可为空，外键 → Building.Building_ID）

            表名：Asset_Maintenance（资产检修）
            - Maintenance_ID（检修编号，主键）
            - Asset_ID（资产编号，外键 → Asset.Asset_ID）
            - Date（检修时间）
            - Technician（检修人）
            - Result（检修结论）
            - Notes（备注）

            表名：Tutor（导师）
            - Tutor_ID（导师ID，主键）
            - Assigned_Floor（管理楼层）
            - Name（姓名）
            - Email（邮箱）
            - Office_Location（办公室位置）
            - Warden_ID（负责楼栋的舍监ID，外键 → Warden.Warden_ID）

            仅根据上方结构生成 SQL 查询语句，不输出解释说明，也不要使用不存在的表名或字段名。
            """
            },
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"-- DeepSeek 请求失败：{e}"

#密钥配置
app.secret_key = '一个非常随机的密钥'

#登陆界面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            session.permanent = False  # ✅ 非持久性 Session（浏览器关了就失效）
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.before_request
def require_login():
    if request.endpoint and not request.endpoint.startswith('static'):
        if not session.get('logged_in') and request.endpoint != 'login':
            return redirect(url_for('login'))

#主页
@app.route('/')
def index():
    return render_template('index.html')

# 通用页面路由生成器

def generate_entity_route(endpoint, template_name, table_name, primary_key):
    def route():
        conn = get_db_connection()
        cursor = conn.cursor()
        sql_result = None
        generated_sql = None

        if request.method == 'POST':
            action = request.form.get("form_action")

            if action == "query" and 'query_prompt' in request.form:
                prompt = request.form['query_prompt']
                generated_sql = call_deepseek(prompt)
                generated_sql = re.sub(r"(?i)^```?sql\s*", "", generated_sql).strip()
                generated_sql = re.sub(r"```$", "", generated_sql).strip()
                try:
                    cursor.execute(generated_sql)
                    sql_result = cursor.fetchall()
                except Exception as e:
                    sql_result = [{"错误": f"SQL 执行错误：{e}"}]

            elif action == "insert":
                cols = [k for k in request.form.keys() if k not in ["form_action"]]
                vals = [request.form[k] for k in cols]
                placeholders = ", ".join(["%s"] * len(cols))
                col_names = ", ".join(cols)
                sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
                try:
                    cursor.execute(sql, vals)
                    conn.commit()
                except Exception as e:
                    sql_result = [{"错误": f"插入失败：{e}"}]

            elif action == "delete":
                pk_val = request.form.get(primary_key)
                try:
                    cursor.execute(f"DELETE FROM {table_name} WHERE {primary_key} = %s", (pk_val,))
                    conn.commit()
                except Exception as e:
                    sql_result = [{"错误": f"删除失败：{e}"}]

            elif action == "update":
                cols = [k for k in request.form.keys() if k not in ["form_action", primary_key]]
                vals = [request.form[k] for k in cols]
                pk_val = request.form.get(primary_key)
                set_clause = ", ".join([f"{col} = %s" for col in cols])
                sql = f"UPDATE {table_name} SET {set_clause} WHERE {primary_key} = %s"
                try:
                    cursor.execute(sql, vals + [pk_val])
                    conn.commit()
                except Exception as e:
                    sql_result = [{"错误": f"更新失败：{e}"}]

        cursor.execute(f"SELECT * FROM {table_name}")
        records = cursor.fetchall()
        conn.close()
        return render_template(template_name, records=records, sql=generated_sql, result=sql_result)

    app.add_url_rule(f"/{endpoint}", endpoint=f"{endpoint}_view", view_func=route, methods=['GET', 'POST'])


# 注册多个实体路由
generate_entity_route("student", "student.html", "Student", "Student_ID")
generate_entity_route("dorm", "dorm.html", "Dorm", "Dorm_ID")
generate_entity_route("building", "building.html", "Building", "Building_ID")
generate_entity_route("asset", "asset.html", "Asset", "Asset_ID")
generate_entity_route("activity", "activity.html", "Activity", "Activity_ID")
generate_entity_route("tutor", "tutor.html", "Tutor", "Tutor_ID")
generate_entity_route("warden", "warden.html", "Warden", "Warden_ID")
generate_entity_route("asset_maintenance", "asset_maintenance.html", "Asset_Maintenance", "Maintenance_ID")


if __name__ == '__main__':
    app.run(debug=True, host='10.30.76.236')