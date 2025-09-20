const HttpStatus = require('./httpStatus');

const successResponse = (res, { message = 'Success', data = null, statusCode = HttpStatus.OK } = {}) =>
  res.status(statusCode).json({
    status: 'success',
    message,
    data,
  });

const errorResponse = (res, { message = 'Something went wrong', errors, statusCode = HttpStatus.INTERNAL_SERVER_ERROR } = {}) => {
  const payload = {
    status: 'error',
    message,
  };

  if (errors) {
    payload.errors = errors;
  }

  return res.status(statusCode).json(payload);
};

module.exports = {
  successResponse,
  errorResponse,
};
