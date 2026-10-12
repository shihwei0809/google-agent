CREATE TABLE IF NOT EXISTS ipa_data (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE TABLE IF NOT EXISTS ipa_archives (
  id TEXT PRIMARY KEY,
  timestamp TEXT,
  data_json TEXT
);
