const mongoose = require('mongoose');
const schema = new mongoose.Schema({
  id: {type: Number, required: true, unique: true},
  city: String, state: {type: String, index: true}, address: String, zip: String,
  lat: String, long: String, short_name: String, full_name: {type: String, required: true}
}, {versionKey: false});
module.exports = mongoose.model('Dealership', schema);
