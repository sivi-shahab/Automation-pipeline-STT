const itemService = require('../services/itemService');
const HttpStatus = require('../utils/httpStatus');
const { successResponse } = require('../utils/apiResponse');

const getItems = (req, res, next) => {
  try {
    const items = itemService.getItems();
    return successResponse(res, {
      message: 'Items retrieved successfully',
      data: items,
    });
  } catch (error) {
    return next(error);
  }
};

const getItemById = (req, res, next) => {
  try {
    const { id } = req.params;
    const item = itemService.getItemById(Number(id));

    return successResponse(res, {
      message: 'Item retrieved successfully',
      data: item,
    });
  } catch (error) {
    return next(error);
  }
};

const createItem = (req, res, next) => {
  try {
    const { name, description } = req.body;
    const created = itemService.createItem({ name, description });

    return successResponse(res, {
      message: 'Item created successfully',
      data: created,
      statusCode: HttpStatus.CREATED,
    });
  } catch (error) {
    return next(error);
  }
};

const updateItem = (req, res, next) => {
  try {
    const { id } = req.params;
    const { name, description } = req.body;
    const payload = {};

    if (name !== undefined) {
      payload.name = name;
    }

    if (description !== undefined) {
      payload.description = description;
    }

    const updated = itemService.updateItem(Number(id), payload);

    return successResponse(res, {
      message: 'Item updated successfully',
      data: updated,
    });
  } catch (error) {
    return next(error);
  }
};

const deleteItem = (req, res, next) => {
  try {
    const { id } = req.params;
    itemService.deleteItem(Number(id));

    return successResponse(res, {
      message: 'Item deleted successfully',
      data: { id: Number(id) },
      statusCode: HttpStatus.OK,
    });
  } catch (error) {
    return next(error);
  }
};

module.exports = {
  getItems,
  getItemById,
  createItem,
  updateItem,
  deleteItem,
};
