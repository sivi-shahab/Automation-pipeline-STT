const itemRepository = require('../repositories/itemRepository');
const { NotFoundError } = require('../utils/errors');

const getItems = () => itemRepository.findAll();

const getItemById = (id) => {
  const item = itemRepository.findById(id);

  if (!item) {
    throw new NotFoundError(`Item with id ${id} not found`);
  }

  return item;
};

const createItem = (payload) => itemRepository.create(payload);

const updateItem = (id, payload) => {
  const updated = itemRepository.update(id, payload);

  if (!updated) {
    throw new NotFoundError(`Item with id ${id} not found`);
  }

  return updated;
};

const deleteItem = (id) => {
  const wasRemoved = itemRepository.remove(id);

  if (!wasRemoved) {
    throw new NotFoundError(`Item with id ${id} not found`);
  }

  return wasRemoved;
};

module.exports = {
  getItems,
  getItemById,
  createItem,
  updateItem,
  deleteItem,
};
