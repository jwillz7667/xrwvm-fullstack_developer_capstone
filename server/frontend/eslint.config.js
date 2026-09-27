import js from '@eslint/js';
import globals from 'globals';
export default [
  {ignores:['dist/**','node_modules/**']},
  {files:['src/**/*.{js,jsx}'],languageOptions:{ecmaVersion:'latest',sourceType:'module',globals:globals.browser,parserOptions:{ecmaFeatures:{jsx:true}}},rules:{...js.configs.recommended.rules,'no-unused-vars':['error',{varsIgnorePattern:'^[A-Z]',argsIgnorePattern:'^_'}]}},
  {files:['*.config.js'],languageOptions:{ecmaVersion:'latest',sourceType:'module',globals:globals.node},rules:js.configs.recommended.rules}
];
