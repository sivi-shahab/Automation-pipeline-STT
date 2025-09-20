const express = require('express');
const itemRoutes = require('./itemRoutes');

const router = express.Router();

router.use('/items', itemRoutes);

module.exports = router;
