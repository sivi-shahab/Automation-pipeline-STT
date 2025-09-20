let items = [];
let nextId = 1;

const findAll = () => [...items];

const findById = (id) => items.find((item) => item.id === id);

const create = (payload) => {
  const timestamp = new Date().toISOString();
  const newItem = {
    id: nextId++,
    name: payload.name,
    description: payload.description ?? '',
    createdAt: timestamp,
    updatedAt: timestamp,
  };

  items.push(newItem);
  return newItem;
};

const update = (id, payload) => {
  const existingIndex = items.findIndex((item) => item.id === id);

  if (existingIndex === -1) {
    return null;
  }

  const updatedItem = {
    ...items[existingIndex],
    ...payload,
    id,
    updatedAt: new Date().toISOString(),
  };

  items[existingIndex] = updatedItem;
  return updatedItem;
};

const remove = (id) => {
  const initialLength = items.length;
  items = items.filter((item) => item.id !== id);
  return items.length !== initialLength;
};

module.exports = {
  findAll,
  findById,
  create,
  update,
  remove,
};
