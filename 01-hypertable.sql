CREATE TABLE conditions (
  time        TIMESTAMPTZ       NOT NULL,
  location    TEXT              NOT NULL,
  device      TEXT              NOT NULL,
  temperature DOUBLE PRECISION  NULL,
  humidity    DOUBLE PRECISION  NULL
) WITH (
  tsdb.hypertable,
  tsdb.segmentby = 'device',
  tsdb.orderby = 'time DESC'
);

INSERT INTO conditions (time, location, device, temperature, humidity)
VALUES
  (NOW() - INTERVAL '2 hours', 'office', 'sensor-1', 22.1, 45.0),
  (NOW() - INTERVAL '1 hour',  'office', 'sensor-1', 22.3, 44.8),
  (NOW(),                      'office', 'sensor-1', 22.2, 45.1);

SELECT * FROM conditions ORDER BY time DESC;

SELECT hypertable_name, num_dimensions, num_chunks, compression_enabled
FROM timescaledb_information.hypertables;
