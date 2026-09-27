const test = require('node:test');
const assert = require('node:assert/strict');
const mongoose = require('mongoose');
const {randomUUID} = require('node:crypto');
const {createApp, seed} = require('./app');
const Review = require('./review');
const key = 'test-service-key-not-a-production-secret-739';
let server, origin;
test.before(async () => {
  const name = 'test_' + randomUUID().replaceAll('-', '');
  await mongoose.connect(process.env.TEST_MONGODB_URI || 'mongodb://127.0.0.1:27019', {dbName:name});
  await seed();
  server = createApp(key).listen(0, '127.0.0.1');
  await new Promise(resolve => server.once('listening', resolve));
  origin = 'http://127.0.0.1:' + server.address().port;
});
test.after(async () => {if(server) await new Promise(resolve => server.close(resolve));if(mongoose.connection.readyState) await mongoose.connection.dropDatabase();await mongoose.disconnect();});
test('all dealers, Kansas filter, details and reviews match seeded data', async () => {
  const all=await (await fetch(origin+'/fetchDealers')).json();assert.ok(all.length>0);
  const filtered=await (await fetch(origin+'/fetchDealers/Kansas')).json();assert.ok(filtered.length>0);assert.ok(filtered.every(d=>d.state==='Kansas'));
  const detail=await (await fetch(origin+'/fetchDealer/'+all[0].id)).json();assert.equal(detail[0].full_name,all[0].full_name);
  const reviews=await (await fetch(origin+'/fetchReviews/dealer/'+all[0].id)).json();assert.ok(reviews.every(r=>r.dealership===all[0].id));
});
test('writes require service authentication and preserve review across re-seeding', async () => {
  const data={user_id:1,name:'Integration Tester',dealership:1,review:'Fantastic services',purchase:false,sentiment:'positive'};
  let response=await fetch(origin+'/insert_review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});assert.equal(response.status,401);
  response=await fetch(origin+'/insert_review',{method:'POST',headers:{'Content-Type':'application/json','X-Service-Key':key},body:JSON.stringify(data)});assert.equal(response.status,201);
  const saved=await response.json();await seed();assert.ok(await Review.findOne({id:saved.id}));
});
test('malformed identifiers and data cannot become Mongo queries', async () => {
  assert.equal((await fetch(origin+'/fetchDealer/not-a-number')).status,400);
  const response=await fetch(origin+'/insert_review',{method:'POST',headers:{'Content-Type':'application/json','X-Service-Key':key},body:JSON.stringify({dealership:{$ne:null},review:'x'})});assert.equal(response.status,400);
});
