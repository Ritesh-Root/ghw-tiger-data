CREATE MATERIALIZED VIEW sensor_hourly
WITH (timescaledb.continuous) AS
SELECT
  time_bucket('1 hour', time) AS bucket,
  sensor_id,
  AVG(temperature) AS avg_temp,
  MIN(temperature) AS min_temp,
  MAX(temperature) AS max_temp,
  AVG(cpu)         AS avg_cpu,
  COUNT(*)         AS readings
FROM sensor_data
GROUP BY bucket, sensor_id;

-- Keep the aggregate fresh automatically: refresh every 30 minutes over the last 3 days.
SELECT add_continuous_aggregate_policy('sensor_hourly',
  start_offset      => INTERVAL '3 days',
  end_offset        => INTERVAL '1 hour',
  schedule_interval => INTERVAL '30 minutes');

-- Fast dashboard query: hourly averages for sensor 1
SELECT bucket, sensor_id, round(avg_temp::numeric,2) AS avg_temp,
       round(min_temp::numeric,2) AS min_temp, round(max_temp::numeric,2) AS max_temp, readings
FROM sensor_hourly
WHERE sensor_id = 1
ORDER BY bucket DESC
LIMIT 6;

-- Sanity check: aggregate must equal the raw table for the same bucket
SELECT 'cagg' AS source, sum(readings) AS total_readings FROM sensor_hourly
UNION ALL
SELECT 'raw', count(*) FROM sensor_data;

SELECT view_name, materialization_hypertable_name FROM timescaledb_information.continuous_aggregates;
