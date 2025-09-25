-- schema.sql
CREATE SCHEMA IF NOT EXISTS postgres;

-- ENUM: типы атак
CREATE TYPE postgres.attack_type AS ENUM ('UDP_FLOOD', 'SYN_FLOOD', 'HTTP_FLOOD', 'ICMP_FLOOD', 'DNS_AMPLIFICATION');

-- Таблица экспериментов
CREATE TABLE IF NOT EXISTS postgres.experiments (
    experiment_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (name)
);

-- Таблица прогонов (runs) — привязана к эксперименту
CREATE TABLE IF NOT EXISTS postgres.runs (
    run_id SERIAL PRIMARY KEY,
    experiment_id INTEGER NOT NULL REFERENCES postgres.experiments(experiment_id)
        ON DELETE CASCADE  -- если эксперимент удалён — удалить связанные прогоны
        ON UPDATE CASCADE,
    attack_types postgres.attack_type[] NOT NULL, -- массив enum — демонстрация array
    source_ips INET[] , -- массив IP-адресов атакующих (тип inet)
    packet_rate INTEGER NOT NULL CHECK (packet_rate > 0), -- метрика — проверка >0
    detected BOOLEAN DEFAULT FALSE,
    severity VARCHAR(10) CHECK (severity IN ('LOW','MEDIUM','HIGH')) DEFAULT 'MEDIUM',
    run_time TIMESTAMP WITH TIME ZONE DEFAULT now(),
    UNIQUE (experiment_id, run_time) -- пример UNIQUE сочетания
);

-- Таблица метрик (опционально) — демонстрирует FK на run
CREATE TABLE IF NOT EXISTS postgres.metrics (
    metric_id SERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES postgres.runs(run_id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
