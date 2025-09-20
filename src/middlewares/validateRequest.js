const { validationResult } = require('express-validator');
const { ValidationError } = require('../utils/errors');

const validateRequest = (req, res, next) => {
  const errors = validationResult(req);

  if (!errors.isEmpty()) {
    return next(new ValidationError('Request validation failed', errors.array()));
  }

  return next();
};

module.exports = validateRequest;
