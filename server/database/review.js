const mongoose = require('mongoose');
const schema = new mongoose.Schema({
  id: {type: String, required: true, unique: true},
  user_id: Number, name: {type: String, required: true, maxlength: 301},
  dealership: {type: Number, required: true, index: true},
  review: {type: String, required: true, maxlength: 3000},
  purchase: {type: Boolean, required: true}, purchase_date: String,
  car_make: String, car_model: String, car_year: Number,
  time: {type: Date, required: true, default: Date.now},
  sentiment: {type: String, enum: ['positive', 'neutral', 'negative'], default: 'neutral'}
}, {versionKey: false});
schema.index({dealership: 1, time: -1});
module.exports = mongoose.model('Review', schema);
