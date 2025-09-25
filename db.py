# db.py
import os
import logging
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

# Функция для получения параметров подключения (можно заменить на чтение из .env)
def get_conn_params():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "postgres"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "Tyur1234")
    }

def get_connection():
    params = get_conn_params()
    conn = psycopg2.connect(**params)
    conn.autocommit = False  # мы управляем транзакциями
    return conn

def execute_script(sql_text):
    """Выполнить DDL-скрипт (schema.sql)."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql_text)
        conn.commit()
        logger.info("DDL script executed successfully.")
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Error executing script: %s", e)
        raise
    finally:
        if conn:
            conn.close()

def insert_experiment_and_run(experiment_name, experiment_description,
                              attack_types_list, source_ip_list,
                              packet_rate, severity, detected=False):
    """
    Вставляет эксперимент (если не существует с тем же именем) и прогоны в транзакции.
    attack_types_list: list of strings (values of enum)
    source_ip_list: list of ip strings
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 1) Вставляем эксперимент и получаем experiment_id (или находим существующий)
        cur.execute("""
            INSERT INTO postgres.experiments (name, description)
            VALUES (%s, %s)
            ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description
            RETURNING experiment_id;
        """, (experiment_name, experiment_description))
        row = cur.fetchone()
        experiment_id = row[0]

        # 2) Вставляем run
        cur.execute("""
            INSERT INTO postgres.runs (
                experiment_id, attack_types, source_ips, packet_rate, severity, detected
            ) VALUES (%s, %s::postgres.attack_type[], %s::inet[], %s, %s, %s)
            RETURNING run_id;
        """, (experiment_id, attack_types_list, source_ip_list, packet_rate, severity, detected))
        run_id = cur.fetchone()[0]

        conn.commit()
        logger.info("Inserted experiment_id=%s run_id=%s", experiment_id, run_id)
        return experiment_id, run_id

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Error inserting data: %s", e)
        raise
    finally:
        if conn:
            conn.close()

def query_runs(filter_attack_type=None, since=None, min_packet_rate=None):
    """
    Получает список прогонов экспериментов (runs) с опциональными фильтрами.
    Если фильтры не заданы, возвращаются все строки.
    """
    sql = """
        SELECT r.run_id,
               r.experiment_id,
               e.name AS experiment_name,
               r.attack_types,
               r.source_ips,
               r.packet_rate,
               r.severity,
               r.detected,
               r.run_time
        FROM postgres.runs r
        JOIN postgres.experiments e ON r.experiment_id = e.experiment_id
        WHERE 1=1
    """
    params = []

    # Фильтр по типу атаки (если задан)
    if filter_attack_type:
        sql += " AND %s = ANY(r.attack_types)"
        params.append(filter_attack_type)

    # Фильтр по дате
    if since:
        sql += " AND r.run_time >= %s"
        params.append(since)

    # Фильтр по минимальному packet_rate
    if min_packet_rate:
        sql += " AND r.packet_rate >= %s"
        params.append(min_packet_rate)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            # Преобразуем к списку словарей для удобства в PyQt
            return [dict(zip(colnames, row)) for row in rows]

