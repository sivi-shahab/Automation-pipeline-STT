const HttpStatus = require('../utils/httpStatus');
const { AppError } = require('../utils/errors');
const { errorResponse } = require('../utils/apiResponse');

const errorHandler = (err, req, res, next) => {
  const isKnownError = err instanceof AppError;
  const statusCode = isKnownError ? err.statusCode : HttpStatus.INTERNAL_SERVER_ERROR;

  const responsePayload = {
    message: err.message || 'Internal server error',
    statusCode,
  };

  if (err.errors) {
    responsePayload.errors = err.errors;
  }

  if (!isKnownError && process.env.NODE_ENV === 'development') {
    responsePayload.stack = err.stack;
  }

  return errorResponse(res, responsePayload);
};

module.exports = errorHandler;
