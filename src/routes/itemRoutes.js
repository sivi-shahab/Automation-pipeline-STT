const express = require('express');
const itemController = require('../controllers/itemController');
const validateRequest = require('../middlewares/validateRequest');
const { idParamValidator, createItemValidator, updateItemValidator } = require('../validators/itemValidator');

const router = express.Router();

router
  .route('/')
  .get(itemController.getItems)
  .post(createItemValidator, validateRequest, itemController.createItem);

router
  .route('/:id')
  .get(idParamValidator, validateRequest, itemController.getItemById)
  .put([...idParamValidator, ...updateItemValidator], validateRequest, itemController.updateItem)
  .delete(idParamValidator, validateRequest, itemController.deleteItem);

module.exports = router;
