const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');


const app = express();
const port = 3000;


app.use(express.json());
app.use(cors());


const db = new sqlite3.Database('./smart_greenhouse.db', (err) => {
    if (err) {
        console.error('❌ Greška pri spajanju na bazu:', err.message);
    } else {
        console.log('✅ Uspješno spojeno na SQLite bazu.');
    }
});


app.get('/api/readings', (req, res) => {
    const sql = 'SELECT * FROM sensor_readings ORDER BY timestamp DESC LIMIT 1';
    db.get(sql, [], (err, row) => {
        if (err) {
            console.error("❌ Greška pri dohvaćanju podataka iz baze:", err.message);
            res.status(500).json({ error: err.message });
            return;
        }


        if (!row) {
            console.log("⚠ Nema podataka u bazi!");
            res.json({
                temperature: "--", humidity: "--", moisture: "--",
                water_status: "unknown", pump_status: "unknown", fan_status: "unknown"
            });
            return;
        }


        console.log("✅ Najnoviji podaci iz baze:", row);


        let water_status = row.water_level !== undefined && row.water_level === 0 ? "low" : "ok";
        let pump_status = row.moisture < 200 ? "on" : "off";
        let fan_status = row.temperature > 26 ? "on" : "off";


        res.json({
            temperature: row.temperature || "--",
            humidity: row.humidity || "--",
            moisture: row.moisture || "--",
            water_status,
            pump_status,
            fan_status,
            timestamp: row.timestamp || "N/A"
        });
    });
});


app.listen(port, () => {
    console.log(`🚀 Server pokrenut na http://localhost:${port}`);
});
