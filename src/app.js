const PORT = process.env.PORT || 8080;

const express = require('express');
const bodyParser = require('body-parser'); // JSON parsing
const app = express();

const { Client } = require('pg');


let client = null;
const connectDb = async (retries = 5) => {
    while (retries) {
        try {
            await createConnection();
            console.log("Connected to db");
            break;
        } catch (err) {
            //console.log(err);
            retries -= 1;
            console.log("Retries left " + retries);
            await new Promise(res => setTimeout(res, 5000));
        }
    }
}

async function createConnection() {
    client = new Client({
        user: process.env.POSTGRES_USER,
        host: process.env.POSTGRES_HOST,
        database: process.env.POSTGRES_DB,
        password: process.env.POSTGRES_PASSWORD,
        port: process.env.POSTGRES_PORT,
    });
    await client.connect();
};

connectDb();

app.listen(PORT, () => {
    console.log("Backend started on 8080");
    console.log(process.env.POSTGRES_DB);
});

app.get('/api', function (req, res) {
    res.send('API is running');
});

app.get('/api/database-connectivity', async (req, res) => {
    client.query('SELECT NOW() as now')
        .then(r => {
            res.send(
                r.rows[0]
            );
        })
        .catch(e => console.error(e.stack))
});

