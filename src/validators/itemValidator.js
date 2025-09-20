const { body, param } = require('express-validator');

const idParamValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('id must be a positive integer')
    .toInt(),
];

const createItemValidator = [
  body('name')
    .trim()
    .notEmpty()
    .withMessage('name is required')
    .isLength({ max: 100 })
    .withMessage('name must be at most 100 characters long'),
  body('description')
    .optional()
    .isString()
    .withMessage('description must be a string')
    .isLength({ max: 255 })
    .withMessage('description must be at most 255 characters long'),
];

const updateItemValidator = [
  body()
    .custom((value, { req }) => {
      if (req.body.name === undefined && req.body.description === undefined) {
        throw new Error('At least one field (name or description) must be provided');
      }

      return true;
    }),
  body('name')
    .optional()
    .trim()
    .notEmpty()
    .withMessage('name cannot be empty when provided')
    .isLength({ max: 100 })
    .withMessage('name must be at most 100 characters long'),
  body('description')
    .optional()
    .isString()
    .withMessage('description must be a string')
    .isLength({ max: 255 })
    .withMessage('description must be at most 255 characters long'),
];

module.exports = {
  idParamValidator,
  createItemValidator,
  updateItemValidator,
};
