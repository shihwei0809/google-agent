DROP TABLE IF EXISTS DataStore;
CREATE TABLE DataStore (
  key TEXT PRIMARY KEY,
  value TEXT
);

DROP TABLE IF EXISTS ArchiveStore;
CREATE TABLE ArchiveStore (
  id TEXT PRIMARY KEY,
  timestamp TEXT,
  dataJSON TEXT
);

-- Initialize default keys to prevent empty UI
INSERT INTO DataStore (key, value) VALUES ('startDateTime', '');
INSERT INTO DataStore (key, value) VALUES ('scheduleStartDateTime', '');
INSERT INTO DataStore (key, value) VALUES ('totalTonnage', '');
INSERT INTO DataStore (key, value) VALUES ('flowRate', '');
INSERT INTO DataStore (key, value) VALUES ('carCapacity', '');
INSERT INTO DataStore (key, value) VALUES ('yieldRate', '');
INSERT INTO DataStore (key, value) VALUES ('safetyStock', '');
INSERT INTO DataStore (key, value) VALUES ('initialStockDay0', '');
INSERT INTO DataStore (key, value) VALUES ('stockTK623', '');
INSERT INTO DataStore (key, value) VALUES ('stockTK689', '');
INSERT INTO DataStore (key, value) VALUES ('stockTK692', '');
INSERT INTO DataStore (key, value) VALUES ('manualInputs', '{}');
INSERT INTO DataStore (key, value) VALUES ('scheduleInputs', '{}');
INSERT INTO DataStore (key, value) VALUES ('carSequence', '[]');
