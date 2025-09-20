const express = require('express');
const morgan = require('morgan');
const cors = require('cors');
const routes = require('./routes');
const notFoundHandler = require('./middlewares/notFoundHandler');
const errorHandler = require('./middlewares/errorHandler');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.use(morgan('dev'));

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.use('/api', routes);

app.use(notFoundHandler);
app.use(errorHandler);

module.exports = app;
