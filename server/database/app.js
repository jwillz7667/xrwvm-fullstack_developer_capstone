const express = require('express');
const mongoose = require('mongoose');
const helmet = require('helmet');
const {rateLimit} = require('express-rate-limit');
const {randomUUID, timingSafeEqual} = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const Dealership = require('./dealership');
const Review = require('./review');

function validId(value) {
  return /^\d{1,9}$/.test(String(value)) && Number(value) > 0;
}
function createApp(serviceKey) {
  if (!serviceKey || serviceKey.length < 32) throw new Error('Set a SERVICE_KEY of at least 32 characters');
  const app = express();
  app.disable('x-powered-by');
  app.use(helmet());
  app.use(rateLimit({windowMs: 60000, limit: 300, standardHeaders: 'draft-8', legacyHeaders: false}));
  app.use(express.json({limit: '16kb'}));
  app.get('/healthz', (_req, res) => res.status(mongoose.connection.readyState === 1 ? 200 : 503).json({status: mongoose.connection.readyState === 1 ? 'ok' : 'unavailable'}));
  app.get('/fetchDealers', async (_req, res) => res.json(await Dealership.find().sort({id: 1}).lean()));
  app.get('/fetchDealers/:state', async (req, res) => {
    if (req.params.state.length > 50) return res.status(400).json({error: 'Invalid state'});
    res.json(await Dealership.find({state: req.params.state}).sort({id: 1}).lean());
  });
  app.get('/fetchDealer/:id', async (req, res) => {
    if (!validId(req.params.id)) return res.status(400).json({error: 'Invalid dealer ID'});
    res.json(await Dealership.find({id: Number(req.params.id)}).lean());
  });
  app.get('/fetchReviews', async (_req, res) => res.json(await Review.find().sort({time: -1, _id: -1}).limit(500).lean()));
  app.get('/fetchReviews/dealer/:id', async (req, res) => {
    if (!validId(req.params.id)) return res.status(400).json({error: 'Invalid dealer ID'});
    res.json(await Review.find({dealership: Number(req.params.id)}).sort({time: -1, _id: -1}).limit(200).lean());
  });
  app.post('/insert_review', async (req, res) => {
    const supplied = Buffer.from(req.get('X-Service-Key') || '');
    const expected = Buffer.from(serviceKey);
    if (supplied.length !== expected.length || !timingSafeEqual(supplied, expected)) return res.status(401).json({error: 'Authentication required'});
    const data = req.body;
    if (!data || Array.isArray(data) || typeof data !== 'object') return res.status(400).json({error: 'Expected a review object'});
    if (typeof data.review !== 'string' || !data.review.trim() || data.review.length > 3000 || typeof data.name !== 'string' || !data.name.trim() || data.name.length > 301 || !Number.isSafeInteger(data.dealership) || data.dealership <= 0 || !Number.isSafeInteger(data.user_id) || data.user_id <= 0 || typeof data.purchase !== 'boolean' || !['positive', 'neutral', 'negative'].includes(data.sentiment)) return res.status(400).json({error: 'Invalid review fields'});
    if (data.purchase && (typeof data.car_make !== 'string' || !data.car_make || data.car_make.length > 60 || typeof data.car_model !== 'string' || !data.car_model || data.car_model.length > 80 || !Number.isInteger(data.car_year) || data.car_year < 1900 || data.car_year > 2100 || !/^\d{4}-\d{2}-\d{2}$/.test(data.purchase_date) || !Number.isFinite(Date.parse(data.purchase_date)) || Date.parse(data.purchase_date) > Date.now())) return res.status(400).json({error: 'Invalid purchase details'});
    if (!await Dealership.exists({id: data.dealership})) return res.status(404).json({error: 'Dealer not found'});
    const review = await Review.create({id: randomUUID(), user_id: data.user_id, name: data.name.trim(), dealership: data.dealership, review: data.review.trim(), purchase: data.purchase, purchase_date: data.purchase ? data.purchase_date : '', car_make: data.purchase ? data.car_make : '', car_model: data.purchase ? data.car_model : '', car_year: data.purchase ? data.car_year : null, time: new Date(), sentiment: data.sentiment});
    return res.status(201).json(review);
  });
  app.use((_req, res) => res.status(404).json({error: 'Endpoint not found'}));
  app.use((error, _req, res, _next) => {
    const status = error.type === 'entity.too.large' ? 413 : error instanceof SyntaxError || error.name === 'ValidationError' ? 400 : 500;
    if (status === 500) console.error('Dealer service error:', error.name);
    res.status(status).json({error: status === 500 ? 'Dealer service unavailable' : 'Invalid request'});
  });
  return app;
}
async function seed() {
  const read = name => JSON.parse(fs.readFileSync(path.join(__dirname, 'data', name), 'utf8'));
  const dealers = read('dealerships.json').dealerships;
  await Dealership.bulkWrite(dealers.map(item => ({updateOne: {filter: {id: item.id}, update: {$setOnInsert: item}, upsert: true}})));
  const reviews = read('reviews.json').reviews;
  await Review.bulkWrite(reviews.map(item => ({updateOne: {filter: {id: 'seed-' + item.id}, update: {$setOnInsert: {...item, id: 'seed-' + item.id, time: new Date('2024-01-01T00:00:00Z'), sentiment: 'neutral'}}, upsert: true}})));
}
async function main() {
  const app = createApp(process.env.SERVICE_KEY);
  await mongoose.connect(process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/openroad', {serverSelectionTimeoutMS: 10000});
  await Promise.all([Dealership.init(), Review.init()]);
  await seed();
  const server = app.listen(Number(process.env.PORT || 3030), '0.0.0.0', () => console.log('Dealer service listening'));
  for (const signal of ['SIGTERM', 'SIGINT']) process.once(signal, () => {
    server.close(async () => {await mongoose.disconnect(); process.exit(0);});
    setTimeout(() => process.exit(1), 10000).unref();
  });
}
if (require.main === module) main().catch(error => {console.error(error.name, error.message); process.exit(1);});
module.exports = {createApp, seed};
