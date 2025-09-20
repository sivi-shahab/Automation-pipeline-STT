const { NotFoundError } = require('../utils/errors');

const notFoundHandler = (req, res, next) => {
  next(new NotFoundError(`Cannot find ${req.originalUrl}`));
};

module.exports = notFoundHandler;
