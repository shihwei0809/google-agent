export async function onRequestGet(context) {
  const { env } = context;
  try {
    const { results: dataResults } = await env.DB.prepare('SELECT * FROM DataStore').all();
    const resultObj = {};
    
    for (const row of dataResults) {
      const key = row.key;
      let val = row.value;
      if (key === 'startDateTime' || key === 'scheduleStartDateTime') {
        resultObj[key] = val;
        continue;
      }
      try {
        if (typeof val === 'string' && (val.startsWith('{') || val.startsWith('['))) {
          resultObj[key] = JSON.parse(val);
        } else {
          resultObj[key] = val;
        }
      } catch (e) {
        resultObj[key] = val;
      }
    }

    const { results: archiveResults } = await env.DB.prepare('SELECT * FROM ArchiveStore ORDER BY timestamp DESC').all();
    const archiveList = archiveResults.map(row => ({
      id: row.id,
      time: row.timestamp,
      dataStr: row.dataJSON
    }));

    return new Response(JSON.stringify({ 
      data: resultObj, 
      archiveList: archiveList 
    }), {
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (err) {
    return new Response(JSON.stringify({ _error: err.toString() }), { status: 500 });
  }
}
