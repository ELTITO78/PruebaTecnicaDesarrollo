export class ApiError extends Error {}

const request = async (path, signal) => {
  let response;
  try {
    response = await fetch(`/api${path}`, { signal });
  } catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new ApiError('No fue posible conectar con el servidor.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(body.detail ?? 'Ocurrió un error inesperado.');
  }
  return response.json();
};

export const fetchPokemon = ({ page, size, name, type }, signal) => {
  const params = new URLSearchParams({ page, size });
  if (name) params.set('name', name);
  if (type) params.set('type', type);
  return request(`/pokemon?${params}`, signal);
};

export const fetchTypes = () => request('/types');
