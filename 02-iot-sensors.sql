CREATE TABLE sensors(
  id SERIAL PRIMARY KEY,
  type VARCHAR(50),
  location VARCHAR(50)
);

CREATE TABLE sensor_data (
  time TIMESTAMPTZ NOT NULL,
  sensor_id INTEGER,
  temperature DOUBLE PRECISION,
  cpu DOUBLE PRECISION,
  FOREIGN KEY (sensor_id) REFERENCES sensors (id)
) WITH (
  tsdb.hypertable
);

INSERT INTO sensors (type, location) VALUES
  ('a','floor'),
  ('a', 'ceiling'),
  ('b','floor'),
  ('b', 'ceiling');

SELECT * FROM sensors;

INSERT INTO sensor_data (time, sensor_id, cpu, temperature)
SELECT
  time,
  sensor_id,
  random() AS cpu,
  random()*100 AS temperature
FROM generate_series(now() - interval '24 hour', now(), interval '5 minute') AS g1(time),
     generate_series(1,4,1) AS g2(sensor_id);

SELECT count(*) AS rows_generated, min(time) AS first_reading, max(time) AS last_reading FROM sensor_data;

SELECT
  sensors.location,
  time_bucket('30 minutes', time) AS period,
  AVG(temperature) AS avg_temp,
  last(temperature, time) AS last_temp,
  AVG(cpu) AS avg_cpu
FROM sensor_data JOIN sensors ON sensor_data.sensor_id = sensors.id
GROUP BY period, sensors.location
ORDER BY period DESC, sensors.location
LIMIT 8;
