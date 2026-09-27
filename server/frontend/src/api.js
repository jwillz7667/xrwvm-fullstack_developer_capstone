export async function api(path, body) {
  const token = document.cookie.split('; ').find(value => value.startsWith('csrftoken='))?.split('=')[1];
  const response = await fetch('/djangoapp/' + path, {credentials:'same-origin', headers: {'Content-Type':'application/json', ...(body ? {'X-CSRFToken':decodeURIComponent(token || '')} : {})}, method: body ? 'POST' : 'GET', ...(body ? {body:JSON.stringify(body)} : {})});
  let result;
  try { result = await response.json(); } catch { throw new Error('The service could not complete the request. Please try again.'); }
  if (!response.ok) throw new Error(result.error || 'The request could not be completed.');
  return result;
}
