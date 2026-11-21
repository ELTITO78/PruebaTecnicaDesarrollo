import { ApiError, fetchPokemon, fetchTypes } from './api.js';
import { debounce } from './utils.js';

const PAGE_SIZE = 20;
const $ = (selector) => document.querySelector(selector);

const state = { page: 1, name: '', type: '' };
let controller;

const setStatus = (message, kind = '') => {
  $('#status').textContent = message;
  $('#status').className = kind;
};

const renderCard = ({ id, name, image, types }) => {
  const card = $('#card').content.cloneNode(true);
  const img = card.querySelector('img');
  img.src = image ?? '';
  img.alt = name;
  card.querySelector('.id').textContent = `#${String(id).padStart(3, '0')}`;
  card.querySelector('h2').textContent = name;
  card.querySelector('.types').append(...types.map((type) => {
    const badge = document.createElement('span');
    badge.className = 'type';
    badge.textContent = type;
    return badge;
  }));
  return card;
};

const renderPager = ({ page, pages }) => {
  $('#pager').hidden = pages <= 1;
  $('#page-info').textContent = `Página ${page} de ${pages}`;
  $('#prev').disabled = page <= 1;
  $('#next').disabled = page >= pages;
};

const load = async () => {
  controller?.abort();
  controller = new AbortController();
  setStatus('Cargando Pokémon...', 'loading');
  $('#grid').replaceChildren();
  $('#pager').hidden = true;
  try {
    const data = await fetchPokemon({ ...state, size: PAGE_SIZE }, controller.signal);
    $('#grid').replaceChildren(...data.results.map(renderCard));
    renderPager(data);
    setStatus(data.count ? '' : 'No se encontraron Pokémon con esos criterios.');
  } catch (error) {
    if (error.name === 'AbortError') return;
    setStatus(error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.', 'error');
  }
};

const update = (changes) => {
  Object.assign(state, changes);
  load();
};

const loadTypes = async () => {
  try {
    const types = await fetchTypes();
    $('#type').append(...types.map((type) => new Option(type, type)));
  } catch {
    $('#type').disabled = true;
  }
};

$('#filters').addEventListener('submit', (event) => event.preventDefault());
$('#name').addEventListener('input', debounce((event) => update({ name: event.target.value.trim(), page: 1 }), 300));
$('#type').addEventListener('change', (event) => update({ type: event.target.value, page: 1 }));
$('#prev').addEventListener('click', () => update({ page: state.page - 1 }));
$('#next').addEventListener('click', () => update({ page: state.page + 1 }));

loadTypes();
load();
